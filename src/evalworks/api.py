from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from evalworks.db import SessionLocal
from evalworks.llm import LLMUnavailable, chat, propose_probe_cases
from evalworks.models import EvaluationRun, ReviewFeedback
from evalworks.privacy import digest_payload, redact_result
from evalworks.projects import PROJECT_BY_SLUG, PROJECTS
from evalworks.schemas import ChatInput, EvaluationInput, FeedbackInput, ProbePlanInput
from evalworks.security import require_api_key

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/projects")
def list_projects():
    return [
        {"slug": project.slug, "name": project.name, "purpose": project.purpose}
        for project in PROJECTS
    ]


@router.post("/projects/{slug}/evaluate", status_code=status.HTTP_201_CREATED)
def evaluate_project(slug: str, request: EvaluationInput, db: Session = Depends(get_db)):
    project = PROJECT_BY_SLUG.get(slug)
    if project is None:
        raise HTTPException(status_code=404, detail="Unknown project")
    try:
        result = project.evaluator(request.payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    run = EvaluationRun(
        project=slug,
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
def list_runs(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    runs = db.scalars(
        select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit)
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
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(EvaluationRun, run_id)
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
def add_feedback(run_id: str, request: FeedbackInput, db: Session = Depends(get_db)):
    if db.get(EvaluationRun, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    feedback = ReviewFeedback(
        run_id=run_id,
        reviewer_id=request.reviewer_id,
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
def delete_run(run_id: str, db: Session = Depends(get_db)):
    if db.get(EvaluationRun, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    db.execute(delete(ReviewFeedback).where(ReviewFeedback.run_id == run_id))
    db.execute(delete(EvaluationRun).where(EvaluationRun.id == run_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/agents/probe-plan")
def draft_probe_plan(request: ProbePlanInput):
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
def chat_with_model(request: ChatInput):
    total_characters = sum(len(turn.content) for turn in request.messages)
    if total_characters > 32000:
        raise HTTPException(status_code=413, detail="Conversation exceeds 32000 characters")
    try:
        return chat([turn.model_dump() for turn in request.messages])
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
