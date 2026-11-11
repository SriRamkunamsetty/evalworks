from fastapi import APIRouter, HTTPException, status

from owaspbench.dataset.catalog import get_all_benchmark_items
from owaspbench.evaluator.engine import OWASPBenchmarkEngine
from owaspbench.models import (
    BenchmarkItem,
    BenchmarkReport,
    BenchmarkRequest,
    OWASPCategory,
)

router = APIRouter(prefix="/api/v1")
engine = OWASPBenchmarkEngine()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "OWASPTop10Bench"}


@router.get("/categories", response_model=list[dict[str, str]])
def get_categories():
    return [{"id": cat.name, "value": cat.value} for cat in OWASPCategory]


@router.get("/dataset", response_model=list[BenchmarkItem])
def get_dataset():
    return get_all_benchmark_items()


@router.post("/benchmark", response_model=BenchmarkReport)
def run_benchmark(request: BenchmarkRequest):
    try:
        return engine.run_benchmark(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
