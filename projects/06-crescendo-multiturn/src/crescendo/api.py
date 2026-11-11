from fastapi import APIRouter, HTTPException, status

from crescendo.engine.scenarios import list_scenarios
from crescendo.engine.simulator import CrescendoSimulator
from crescendo.models import (
    CrescendoAuditReport,
    CrescendoAuditRequest,
    CrescendoScenario,
)

router = APIRouter(prefix="/api/v1")
simulator = CrescendoSimulator()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "CrescendoSimulator"}


@router.get("/scenarios", response_model=list[CrescendoScenario])
def get_scenarios():
    return list_scenarios()


@router.post("/simulate", response_model=CrescendoAuditReport)
def run_simulation(request: CrescendoAuditRequest):
    try:
        return simulator.run_simulation(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
