from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from agenthijack.engine.auditor import AgentAuditor
from agenthijack.engine.probes import list_probes
from agenthijack.models import (
    AgentAuditReport,
    AgentAuditRequest,
    HijackProbe,
    SecurityPolicyMode,
    ToolCall,
    ToolDefinition,
    ToolExecutionResult,
)
from agenthijack.tools.registry import ToolRegistry

router = APIRouter(prefix="/api/v1")
auditor = AgentAuditor()
registry = ToolRegistry()


class SimulateToolRequest(BaseModel):
    tool_call: ToolCall
    policy_mode: SecurityPolicyMode = SecurityPolicyMode.STRICT_LEAST_PRIVILEGE


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "AgentHijackAuditor"}


@router.get("/tools", response_model=list[ToolDefinition])
def get_available_tools():
    return registry.list_definitions()


@router.get("/probes", response_model=list[HijackProbe])
def get_probes():
    return list_probes()


@router.post("/audit", response_model=AgentAuditReport)
def run_agent_audit(request: AgentAuditRequest):
    try:
        return auditor.run_audit(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/simulate-tool", response_model=ToolExecutionResult)
def simulate_tool_execution(req: SimulateToolRequest):
    tool = registry.get_tool(req.tool_call.tool_name)
    if not tool:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{req.tool_call.tool_name}' not found.",
        )
    return tool.execute(
        arguments=req.tool_call.arguments,
        policy_mode=req.policy_mode,
        call_id=req.tool_call.call_id,
    )
