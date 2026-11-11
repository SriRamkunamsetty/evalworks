from fastapi import APIRouter, HTTPException, status

from calibrator.dataset.pairs import list_contrast_pairs
from calibrator.engine.evaluator import SafetyCalibratorEngine
from calibrator.models import CalibrationReport, CalibrationRequest, ContrastPair

router = APIRouter(prefix="/api/v1")
engine = SafetyCalibratorEngine()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "SafetyRubricCalibrator"}


@router.get("/pairs", response_model=list[ContrastPair])
def get_contrast_pairs():
    return list_contrast_pairs()


@router.post("/calibrate", response_model=CalibrationReport)
def run_calibration(request: CalibrationRequest):
    try:
        return engine.run_calibration(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
