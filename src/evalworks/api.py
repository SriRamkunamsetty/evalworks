from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
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
from evalworks.llm import LLMUnavailable, chat, propose_probe_cases
from evalworks.models import EvaluationRun, ReviewFeedback, User
from evalworks.privacy import digest_payload, redact_result
from evalworks.projects import PROJECT_BY_SLUG, PROJECTS
from evalworks.schemas import (
    ChatInput,
    EvaluationInput,
    FeedbackInput,
    LoginInput,
    ProbeExecutionInput,
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


@router.post("/projects/probefleet/execute", status_code=status.HTTP_201_CREATED)
def execute_probefleet(
    request: ProbeExecutionInput,
    actor: Actor = Depends(require_roles("admin", "reviewer")),
    db: Session = Depends(get_db),
):
    """Run a small, explicitly authorized suite against the server-configured model."""
    from evalworks.evaluators.safety import evaluate as evaluate_safety

    cases = []
    try:
        for case in request.cases:
            model_result = chat([{"role": "user", "content": case.prompt}])
            safe_response = model_result["content"][:8000]
            cases.append(
                {
                    "case_id": case.case_id,
                    "risk_hypothesis": case.risk_hypothesis,
                    "expected_behavior": case.expected_behavior,
                    "response": safe_response,
                    "model": model_result["model"],
                    "latency_ms": model_result["latency_ms"],
                    "triage": evaluate_safety({"prompt": case.prompt, "response": safe_response}),
                    "status": "requires-human-review",
                }
            )
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result = {
        "status": "completed",
        "case_count": len(cases),
        "cases": cases,
        "human_review_required": True,
        "notes": [
            "Only the configured provider was used; no caller-supplied target URL is accepted.",
            "Review each response and triage signal before classifying a finding.",
        ],
    }
    run = EvaluationRun(
        project="probefleet",
        workspace_id=actor.workspace_id,
        created_by=None if actor.id == "local" else actor.id,
        input_digest=digest_payload({"cases": [case.model_dump() for case in request.cases]}),
        result=redact_result(result),
        run_metadata={"provider": "configured-openai-compatible", "evaluator_version": "1.0.0"},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {
        "id": run.id,
        "project": run.project,
        "input_digest": run.input_digest,
        "result": result,
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
