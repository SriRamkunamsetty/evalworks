import pytest

from evalworks.projects import PROJECTS

SAMPLES = {
    "human-eval-studio": {
        "conversation": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello."},
        ]
    },
    "probefleet": {"objective": "clarification", "prompts": ["Ask a clarifying question"]},
    "judgebench": {"human_score": 3, "judge_score": 3, "scale": 5},
    "memory-bench": {"expected_facts": ["likes tea"], "answer": "The user likes tea."},
    "evidencecheck": {"claims": [{"claim": "Claim", "reviewer_verdict": "unreviewed"}]},
    "indiceval": {"language": "Hindi", "prompt": "नमस्ते", "answer": "नमस्ते"},
    "safety-lab": {"prompt": "Hello", "response": "Hi", "severity": "low"},
    "accessibility-reviewer": {"answer": "Clear and simple."},
    "multimodal-qa": {"modalities": ["image"], "expected_observations": ["A red sign"]},
    "evalsre": {
        "title": "Bad answer",
        "finding": "It was wrong.",
        "test_prompt": "Question?",
        "expected_behavior": "Ask for a reliable source.",
        "severity": "medium",
    },
}


@pytest.mark.parametrize("project", PROJECTS, ids=lambda project: project.slug)
def test_each_project_has_a_persisted_evaluation_flow(client, auth_headers, project):
    response = client.post(
        f"/api/v1/projects/{project.slug}/evaluate",
        json={
            "payload": SAMPLES[project.slug],
            "run_metadata": {"model": "sample-model", "prompt_version": "v1"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["project"] == project.slug
    assert len(body["input_digest"]) == 64
    assert body["result"]["human_review_required"] is True
    stored = client.get(f"/api/v1/runs/{body['id']}", headers=auth_headers)
    assert stored.status_code == 200
    assert stored.json()["result"]["human_review_required"] is True
    assert "conversation" not in stored.json()["result"]
    assert len(stored.json()["input_digest"]) == 64
    assert stored.json()["metadata"]["model"] == "sample-model"


def test_api_requires_key(client):
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


def test_feedback_attaches_to_reviewed_run(client, auth_headers):
    run = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json={"payload": SAMPLES["judgebench"]},
        headers=auth_headers,
    ).json()
    response = client.post(
        f"/api/v1/runs/{run['id']}/feedback",
        json={"label": "disagreement", "rationale": "The criteria were interpreted differently."},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["run_id"] == run["id"]


def test_invalid_payload_returns_validation_error(client, auth_headers):
    response = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json={"payload": {"human_score": 9}},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_run_metadata_rejects_prompt_content(client, auth_headers):
    response = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json={"payload": SAMPLES["judgebench"], "run_metadata": {"prompt": "private text"}},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_agent_is_explicitly_disabled_without_llm_settings(client, auth_headers):
    response = client.post(
        "/api/v1/agents/probe-plan", json={"objective": "Test a chatbot"}, headers=auth_headers
    )
    assert response.status_code == 503


def test_live_chat_validates_roles(client, auth_headers):
    response = client.post(
        "/api/v1/models/chat",
        json={"messages": [{"role": "tool", "content": "x"}]},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_live_chat_provider_response_is_not_persisted(client, auth_headers, monkeypatch):
    from evalworks import api

    monkeypatch.setattr(
        api, "chat", lambda messages: {"content": "Hello there", "model": "mock", "latency_ms": 1}
    )
    response = client.post(
        "/api/v1/models/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Hello there"
    assert client.get("/api/v1/runs", headers=auth_headers).json() == []


def test_run_deletion_removes_evaluation_and_feedback(client, auth_headers):
    run = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json={"payload": SAMPLES["judgebench"]},
        headers=auth_headers,
    ).json()
    client.post(
        f"/api/v1/runs/{run['id']}/feedback",
        json={"label": "reviewed", "rationale": "The evidence was checked."},
        headers=auth_headers,
    )
    response = client.delete(f"/api/v1/runs/{run['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/api/v1/runs/{run['id']}", headers=auth_headers).status_code == 404


def test_web_app_and_readiness_are_available(client):
    assert "EvalWorks" in client.get("/").text
    assert client.get("/chat.css").status_code == 200
    assert client.get("/health/ready").json()["status"] == "ready"


def test_request_body_limit_rejects_oversized_input(client):
    response = client.post("/api/v1/models/chat", content=b"x" * 65_537)
    assert response.status_code == 413
