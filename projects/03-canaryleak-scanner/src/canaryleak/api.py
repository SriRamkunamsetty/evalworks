from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from canaryleak.engine.canary import generate_canary_token
from canaryleak.engine.extractors import list_probes
from canaryleak.engine.scanner import CanaryScanner
from canaryleak.models import CanaryAuditReport, CanaryAuditRequest, ExtractionProbe

router = APIRouter(prefix="/api/v1")
scanner = CanaryScanner()


class GenerateCanaryResponse(BaseModel):
    uuid_canary: str
    api_key_canary: str
    code_canary: str


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "CanaryLeak"}


@router.get("/techniques", response_model=list[ExtractionProbe])
def get_techniques():
    return list_probes()


@router.post("/scan", response_model=CanaryAuditReport)
def run_canary_audit(request: CanaryAuditRequest):
    try:
        return scanner.run_audit(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate-canaries", response_model=GenerateCanaryResponse)
def generate_sample_canaries():
    return GenerateCanaryResponse(
        uuid_canary=generate_canary_token("uuid").token_value,
        api_key_canary=generate_canary_token("api_key").token_value,
        code_canary=generate_canary_token("code").token_value,
    )
