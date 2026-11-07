from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from evalworks.auth import (
    Actor,
    authenticate_user,
    clear_session_cookies,
    get_db,
    hash_password,
    issue_session,
    require_actor,
    require_roles,
    set_session_cookies,
)
from evalworks.jobs import encrypt_payload
from evalworks.llm import LLMUnavailable, chat, propose_probe_cases
from evalworks.models import EvaluationJob, EvaluationRun, ReviewFeedback, User
from evalworks.privacy import digest_payload, redact_result
from evalworks.projects import PROJECT_BY_SLUG, PROJECTS
from evalworks.schemas import (
    ChatInput,
    EvaluationInput,
    EvaluationJobInput,
    FeedbackInput,
    LoginInput,
    ProbePlanInput,
    UserCreateInput,
)

router = APIRouter(prefix="/api/v1")
auth_router = APIRouter(prefix="/api/v1/auth")


@auth_router.post("/login")
def login(request: LoginInput, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, csrf = issue_session(user)
    set_session_cookies(response, token, csrf)
    return {"id": user.id, "email": user.email, "role": user.role}


@auth_router.post("/logout")
def logout(response: Response):
    clear_session_cookies(response)
    return {"status": "signed_out"}


@auth_router.get("/me")
def current_user(actor: Actor = Depends(require_actor)):
    return {
        "id": actor.id,
        "email": actor.email,
        "role": actor.role,
        "workspace_id": actor.workspace_id,
    }


@router.get("/users")
def list_users(actor: Actor = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    users = db.scalars(
        select(User).where(User.workspace_id == actor.workspace_id).order_by(User.created_at.asc())
    ).all()
    return [
        {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}
        for user in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreateInput,
    actor: Actor = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    email = str(request.email).strip().casefold()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        workspace_id=actor.workspace_id,
        email=email,
        password_hash=hash_password(request.password),
        role=request.role,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from exc
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}


@router.get("/projects")
def list_projects(_actor: Actor = Depends(require_actor)):
    return [
        {"slug": project.slug, "name": project.name, "purpose": project.purpose}
        for project in PROJECTS
    ]


@router.post("/projects/{slug}/evaluate", status_code=status.HTTP_201_CREATED)
def evaluate_project(
    slug: str,
    request: EvaluationInput,
    actor: Actor = Depends(require_roles("admin", "reviewer")),
    db: Session = Depends(get_db),
):
    project = PROJECT_BY_SLUG.get(slug)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")
    try:
        result = project.evaluator(request.payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    run = EvaluationRun(
        project=slug,
        workspace_id=actor.workspace_id,
        created_by=None if actor.id == "local" else actor.id,
        input_digest=digest_payload(request.payload),
        result=redact_result(result),
        run_metadata=request.run_metadata,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {
        "id": run.id,
        "project": run.project,
        "status": run.status,
        "input_digest": run.input_digest,
        "metadata": run.run_metadata,
        "result": result,
    }


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
def submit_evaluation_job(
    request: EvaluationJobInput,
    idempotency_key: str = Header(
        alias="Idempotency-Key", min_length=8, max_length=128, pattern="^[A-Za-z0-9._:-]+$"
    ),
    actor: Actor = Depends(require_roles("admin", "reviewer")),
    db: Session = Depends(get_db),
):
    project = PROJECT_BY_SLUG.get(request.project)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")
    input_digest = digest_payload(request.payload)
    existing = db.scalar(
        select(EvaluationJob).where(
            EvaluationJob.workspace_id == actor.workspace_id,
            EvaluationJob.idempotency_key == idempotency_key,
        )
    )
    if existing:
        if existing.input_digest != input_digest or existing.project != request.project:
            raise HTTPException(
                status_code=409, detail="Idempotency key was already used for a different request"
            )
        return {"id": existing.id, "status": existing.status, "run_id": existing.run_id}
    active_jobs = db.scalar(
        select(func.count())
        .select_from(EvaluationJob)
        .where(
            EvaluationJob.workspace_id == actor.workspace_id,
            EvaluationJob.status.in_(("queued", "running")),
        )
    )
    if active_jobs >= 100:
        raise HTTPException(status_code=429, detail="Workspace evaluation queue is full")
    job = EvaluationJob(
        workspace_id=actor.workspace_id,
        created_by=None if actor.id == "local" else actor.id,
        project=request.project,
        idempotency_key=idempotency_key,
        input_digest=input_digest,
        payload_ciphertext=encrypt_payload(request.payload),
        metadata_json=request.run_metadata,
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.scalar(
            select(EvaluationJob).where(
                EvaluationJob.workspace_id == actor.workspace_id,
                EvaluationJob.idempotency_key == idempotency_key,
            )
        )
        if (
            existing
            and existing.input_digest == input_digest
            and existing.project == request.project
        ):
            return {"id": existing.id, "status": existing.status, "run_id": existing.run_id}
        raise HTTPException(status_code=409, detail="Idempotency key conflict") from exc
    db.refresh(job)
    return {"id": job.id, "status": job.status, "run_id": None}


@router.get("/jobs/{job_id}")
def get_evaluation_job(
    job_id: str, actor: Actor = Depends(require_actor), db: Session = Depends(get_db)
):
    job = db.scalar(
        select(EvaluationJob).where(
            EvaluationJob.id == job_id,
            EvaluationJob.workspace_id == actor.workspace_id,
        )
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "project": job.project,
        "status": job.status,
        "attempts": job.attempts,
        "run_id": job.run_id,
        "error_code": job.error_code,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("/runs")
def list_runs(
    limit: int = Query(default=50, ge=1, le=100),
    actor: Actor = Depends(require_actor),
    db: Session = Depends(get_db),
):
    runs = db.scalars(
        select(EvaluationRun)
        .where(EvaluationRun.workspace_id == actor.workspace_id)
        .order_by(EvaluationRun.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": run.id,
            "project": run.project,
            "status": run.status,
            "input_digest": run.input_digest,
            "metadata": run.run_metadata,
            "created_at": run.created_at,
        }
        for run in runs
    ]


@router.get("/runs/{run_id}")
def get_run(run_id: str, actor: Actor = Depends(require_actor), db: Session = Depends(get_db)):
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id, EvaluationRun.workspace_id == actor.workspace_id
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "project": run.project,
        "status": run.status,
        "input_digest": run.input_digest,
        "metadata": run.run_metadata,
        "result": run.result,
        "created_at": run.created_at,
    }


@router.post("/runs/{run_id}/feedback", status_code=status.HTTP_201_CREATED)
def add_feedback(
    run_id: str,
    request: FeedbackInput,
    actor: Actor = Depends(require_roles("admin", "reviewer")),
    db: Session = Depends(get_db),
):
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id, EvaluationRun.workspace_id == actor.workspace_id
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    feedback = ReviewFeedback(
        run_id=run_id,
        workspace_id=actor.workspace_id,
        reviewer_id=actor.id,
        label=request.label,
        rationale=request.rationale,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "id": feedback.id,
        "run_id": feedback.run_id,
        "label": feedback.label,
        "created_at": feedback.created_at,
    }


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: str,
    actor: Actor = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id, EvaluationRun.workspace_id == actor.workspace_id
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    db.execute(
        delete(ReviewFeedback).where(
            ReviewFeedback.run_id == run_id, ReviewFeedback.workspace_id == actor.workspace_id
        )
    )
    db.execute(delete(EvaluationRun).where(EvaluationRun.id == run_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/agents/probe-plan")
def draft_probe_plan(
    request: ProbePlanInput,
    _actor: Actor = Depends(require_roles("admin", "reviewer")),
):
    try:
        cases = propose_probe_cases(request.objective, request.count)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "status": "draft",
        "requires_human_approval": True,
        "cases": cases,
        "message": "Review these drafts before adding them to a test set or running them.",
    }


@router.post("/models/chat")
def chat_with_model(
    request: ChatInput, _actor: Actor = Depends(require_roles("admin", "reviewer"))
):
    total_characters = sum(len(turn.content) for turn in request.messages)
    if total_characters > 32000:
        raise HTTPException(status_code=413, detail="Conversation exceeds 32000 characters")
    try:
        return chat([turn.model_dump() for turn in request.messages])
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
