from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

from guardrailgate.engine.evaluator import GuardrailEvaluator
from guardrailgate.engine.suite import get_ci_suite
from guardrailgate.models import GateRunReport, GateRunRequest, GateTestCase
from guardrailgate.reporters.markdown import generate_pr_markdown_summary
from guardrailgate.reporters.sarif import generate_sarif_report

router = APIRouter(prefix="/api/v1")
evaluator = GuardrailEvaluator()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "GuardrailGate"}


@router.get("/suite", response_model=list[GateTestCase])
def get_regression_suite():
    return get_ci_suite()


@router.post("/scan", response_model=GateRunReport)
def run_guardrail_gate(request: GateRunRequest):
    try:
        return evaluator.evaluate_gate(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/export/sarif")
def export_sarif(report: GateRunReport):
    return generate_sarif_report(report)


@router.post("/export/markdown", response_class=PlainTextResponse)
def export_markdown(report: GateRunReport):
    return generate_pr_markdown_summary(report)
