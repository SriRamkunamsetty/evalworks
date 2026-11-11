from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from jailbreaklab.engine import FuzzEngine
from jailbreaklab.models import (
    FuzzCampaignReport,
    FuzzCampaignRequest,
    MutatedPrompt,
    TargetResponse,
    TrialResult,
)
from jailbreaklab.mutators import list_mutators
from jailbreaklab.scorer import evaluate_trial

router = APIRouter(prefix="/api/v1")
engine = FuzzEngine()


class SingleEvaluationRequest(BaseModel):
    mutation: MutatedPrompt
    response: TargetResponse


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "JailbreakLab"}


@router.get("/mutators")
def get_mutators():
    mutators = list_mutators()
    return [
        {
            "id": m.mutator_id.value,
            "name": m.technique_name,
        }
        for m in mutators
    ]


@router.post("/fuzz", response_model=FuzzCampaignReport, status_code=status.HTTP_200_OK)
def run_fuzzing_campaign(request: FuzzCampaignRequest):
    try:
        report = engine.run_campaign(request)
        return report
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Campaign execution failed: {str(exc)}"
        ) from exc


@router.post("/evaluate", response_model=TrialResult, status_code=status.HTTP_200_OK)
def evaluate_single_response(request: SingleEvaluationRequest):
    return evaluate_trial(request.mutation, request.response)
