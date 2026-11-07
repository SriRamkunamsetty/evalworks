import base64
import hashlib
import json
import logging
import time
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import delete, select, update

from evalworks.config import settings
from evalworks.db import SessionLocal
from evalworks.models import EvaluationJob, EvaluationRun, ReviewFeedback
from evalworks.privacy import digest_payload, redact_result
from evalworks.projects import PROJECT_BY_SLUG

logger = logging.getLogger(__name__)
_fernet_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.data_encryption_key.encode()).digest()
)
_fernet = Fernet(_fernet_key)
JOB_LEASE = timedelta(minutes=5)


class InvalidJobPayload(ValueError):
    pass


def encrypt_payload(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return _fernet.encrypt(encoded).decode("ascii")


def decrypt_payload(ciphertext: str) -> dict:
    try:
        value = json.loads(_fernet.decrypt(ciphertext.encode("ascii")))
    except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidJobPayload("Stored job payload cannot be decrypted") from exc
    if not isinstance(value, dict):
        raise InvalidJobPayload("Stored job payload is invalid")
    return value


def claim_one_job(session_factory=SessionLocal) -> str | None:
    now = datetime.now(UTC)
    with session_factory.begin() as db:
        db.execute(
            update(EvaluationJob)
            .where(
                EvaluationJob.status == "running",
                EvaluationJob.locked_until < now,
                EvaluationJob.attempts >= EvaluationJob.max_attempts,
            )
            .values(
                status="failed",
                locked_until=None,
                error_code="worker_lease_expired",
                updated_at=now,
            )
        )
        db.execute(
            update(EvaluationJob)
            .where(
                EvaluationJob.status == "running",
                EvaluationJob.locked_until < now,
                EvaluationJob.attempts < EvaluationJob.max_attempts,
            )
            .values(status="queued", locked_until=None, available_at=now, updated_at=now)
        )
        job = db.scalar(
            select(EvaluationJob)
            .where(EvaluationJob.status == "queued", EvaluationJob.available_at <= now)
            .order_by(EvaluationJob.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if job is None:
            return None
        job.status = "running"
        job.attempts += 1
        job.locked_until = now + JOB_LEASE
        job.updated_at = now
        return job.id


def process_job(job_id: str, session_factory=SessionLocal) -> None:
    with session_factory.begin() as db:
        job = db.get(EvaluationJob, job_id)
        if job is None or job.status != "running":
            return
        project_slug = job.project
        payload_ciphertext = job.payload_ciphertext
        workspace_id = job.workspace_id
        created_by = job.created_by
        run_metadata = job.metadata_json
        input_digest = job.input_digest

    try:
        project = PROJECT_BY_SLUG.get(project_slug)
        if project is None:
            raise InvalidJobPayload("Unknown project")
        payload = decrypt_payload(payload_ciphertext)
        result = project.evaluator(payload)
        run = EvaluationRun(
            project=project_slug,
            workspace_id=workspace_id,
            created_by=created_by,
            input_digest=input_digest or digest_payload(payload),
            result=redact_result(result),
            run_metadata=run_metadata,
        )
        with session_factory.begin() as db:
            job = db.get(EvaluationJob, job_id)
            if job is None or job.status != "running":
                return
            db.add(run)
            db.flush()
            job.run_id = run.id
            job.status = "succeeded"
            job.payload_ciphertext = ""
            job.locked_until = None
            job.updated_at = datetime.now(UTC)
    except Exception as exc:
        logger.error("Evaluation job %s failed with %s", job_id, type(exc).__name__)
        now = datetime.now(UTC)
        with session_factory.begin() as db:
            job = db.get(EvaluationJob, job_id)
            if job is None or job.status != "running":
                return
            job.locked_until = None
            job.updated_at = now
            if isinstance(exc, (InvalidJobPayload, ValueError)) or job.attempts >= job.max_attempts:
                job.status = "failed"
                job.error_code = (
                    "invalid_payload"
                    if isinstance(exc, (InvalidJobPayload, ValueError))
                    else "evaluation_failed"
                )
                job.payload_ciphertext = ""
            else:
                delay_seconds = min(2**job.attempts, 300)
                job.status = "queued"
                job.available_at = now + timedelta(seconds=delay_seconds)


def purge_expired_jobs(session_factory=SessionLocal) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=settings.job_retention_days)
    with session_factory.begin() as db:
        result = db.execute(
            delete(EvaluationJob).where(
                EvaluationJob.status.in_(("succeeded", "failed")),
                EvaluationJob.created_at < cutoff,
            )
        )
        return result.rowcount or 0


def purge_expired_runs(session_factory=SessionLocal) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=settings.run_retention_days)
    with session_factory.begin() as db:
        expired_runs = select(EvaluationRun.id).where(EvaluationRun.created_at < cutoff)
        db.execute(delete(ReviewFeedback).where(ReviewFeedback.run_id.in_(expired_runs)))
        db.execute(
            update(EvaluationJob).where(EvaluationJob.run_id.in_(expired_runs)).values(run_id=None)
        )
        result = db.execute(delete(EvaluationRun).where(EvaluationRun.created_at < cutoff))
        return result.rowcount or 0


def worker_loop(poll_interval: float = 1.0) -> None:
    last_purge = 0.0
    while True:
        if time.monotonic() - last_purge > 3600:
            purge_expired_jobs()
            purge_expired_runs()
            last_purge = time.monotonic()
        job_id = claim_one_job()
        if job_id is None:
            time.sleep(poll_interval)
            continue
        process_job(job_id)
