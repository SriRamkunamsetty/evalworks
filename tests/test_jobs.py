from datetime import UTC, datetime, timedelta

from evalworks.config import settings
from evalworks.jobs import (
    claim_one_job,
    decrypt_payload,
    process_job,
    purge_expired_jobs,
    purge_expired_runs,
)
from evalworks.models import EvaluationJob, EvaluationRun, ReviewFeedback

TEST_HEADERS = {"X-API-Key": settings.api_key}


def submit(client, key, payload=None):
    return client.post(
        "/api/v1/jobs",
        headers={**TEST_HEADERS, "Idempotency-Key": key},
        json={
            "project": "judgebench",
            "payload": payload or {"human_score": 4, "judge_score": 4, "scale": 5},
            "run_metadata": {"model": "test"},
        },
    )


def test_durable_job_is_encrypted_idempotent_and_creates_run(client):
    response = submit(client, "judgebench-job-1")
    assert response.status_code == 202
    job_id = response.json()["id"]
    assert response.json()["status"] == "queued"
    assert submit(client, "judgebench-job-1").json()["id"] == job_id

    with client.app.state.test_session() as db:
        job = db.get(EvaluationJob, job_id)
        assert "human_score" not in job.payload_ciphertext
        assert decrypt_payload(job.payload_ciphertext) == {
            "human_score": 4,
            "judge_score": 4,
            "scale": 5,
        }

    assert claim_one_job(client.app.state.test_session) == job_id
    process_job(job_id, client.app.state.test_session)
    status_response = client.get(
        f"/api/v1/jobs/{job_id}",
        headers=TEST_HEADERS,
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "succeeded"
    run_id = status_response.json()["run_id"]
    run = client.get(
        f"/api/v1/runs/{run_id}",
        headers=TEST_HEADERS,
    )
    assert run.status_code == 200
    assert run.json()["result"]["human_review_required"] is True

    with client.app.state.test_session() as db:
        job = db.get(EvaluationJob, job_id)
        assert job.payload_ciphertext == ""
        job.created_at = datetime.now(UTC) - timedelta(days=31)
        db.commit()
    assert purge_expired_jobs(client.app.state.test_session) == 1
    assert (
        client.get(
            f"/api/v1/jobs/{job_id}",
            headers=TEST_HEADERS,
        ).status_code
        == 404
    )


def test_idempotency_key_cannot_be_reused_for_different_payload(client):
    assert submit(client, "judgebench-job-2").status_code == 202
    response = submit(client, "judgebench-job-2", {"human_score": 1, "judge_score": 1, "scale": 5})
    assert response.status_code == 409


def test_failed_evaluation_is_reported_without_exposing_input(client):
    response = client.post(
        "/api/v1/jobs",
        headers={
            **TEST_HEADERS,
            "Idempotency-Key": "invalid-probe-job",
        },
        json={"project": "probefleet", "payload": {"objective": "Missing prompts"}},
    )
    assert response.status_code == 202
    job_id = response.json()["id"]
    assert claim_one_job(client.app.state.test_session) == job_id
    process_job(job_id, client.app.state.test_session)
    status_response = client.get(
        f"/api/v1/jobs/{job_id}",
        headers=TEST_HEADERS,
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "failed"
    assert status_response.json()["error_code"] == "invalid_payload"
    assert "Missing prompts" not in status_response.text


def test_run_retention_removes_feedback_and_detaches_job(client):
    old_date = datetime.now(UTC) - timedelta(days=400)
    with client.app.state.test_session() as db:
        run = EvaluationRun(
            project="judgebench",
            workspace_id="local",
            input_digest="e" * 64,
            result={"human_review_required": True},
            run_metadata={},
            created_at=old_date,
        )
        db.add(run)
        db.flush()
        feedback = ReviewFeedback(
            run_id=run.id,
            reviewer_id="reviewer",
            workspace_id="local",
            label="reviewed",
            rationale="Checked against the rubric.",
        )
        job = EvaluationJob(
            workspace_id="local",
            project="judgebench",
            idempotency_key="retention-job-key",
            input_digest="e" * 64,
            payload_ciphertext="",
            metadata_json={},
            status="succeeded",
            attempts=1,
            max_attempts=3,
            run_id=run.id,
        )
        db.add_all([feedback, job])
        db.commit()
        run_id, job_id, feedback_id = run.id, job.id, feedback.id

    assert purge_expired_runs(client.app.state.test_session) == 1
    with client.app.state.test_session() as db:
        assert db.get(EvaluationRun, run_id) is None
        assert db.get(ReviewFeedback, feedback_id) is None
        assert db.get(EvaluationJob, job_id).run_id is None
    assert client.get(f"/api/v1/runs/{run_id}", headers=TEST_HEADERS).status_code == 404
