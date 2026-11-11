from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from visionjailbreak.generator.evaluator import VisionJailbreakEvaluator
from visionjailbreak.generator.image_gen import generate_typographic_image
from visionjailbreak.generator.probes import list_vision_probes
from visionjailbreak.models import (
    GeneratedImagePayload,
    PerturbationType,
    VisionAttackProbe,
    VisionAuditReport,
    VisionAuditRequest,
)

router = APIRouter(prefix="/api/v1")
evaluator = VisionJailbreakEvaluator()


class CustomImageGenRequest(BaseModel):
    text: str
    perturbation: PerturbationType = PerturbationType.PLAIN_TYPOGRAPHIC


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "MultimodalVisionJailbreak"}


@router.get("/probes", response_model=list[VisionAttackProbe])
def get_probes():
    return list_vision_probes()


@router.post("/generate-image", response_model=GeneratedImagePayload)
def generate_sample_image(req: CustomImageGenRequest):
    return generate_typographic_image(req.text, req.perturbation)


@router.post("/audit", response_model=VisionAuditReport)
def run_vision_audit(request: VisionAuditRequest):
    try:
        return evaluator.run_audit(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
