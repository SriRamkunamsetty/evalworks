from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolType(StrEnum):
    SQL_QUERY = "sql_query"
    FILE_SYSTEM = "file_system"
    HTTP_FETCH = "http_fetch"
    EMAIL_DISPATCH = "email_dispatch"


class AttackCategory(StrEnum):
    SQL_INJECTION = "sql_injection"
    SSRF_METADATA = "ssrf_metadata"
    PATH_TRAVERSAL = "path_traversal"
    CONFUSED_DEPUTY = "confused_deputy"
    DATA_EXFILTRATION = "data_exfiltration"
    DESTRUCTIVE_EXECUTION = "destructive_execution"
    UNAUTHORIZED_DISPATCH = "unauthorized_dispatch"
    DOS_RESOURCE_EXHAUSTION = "dos_resource_exhaustion"


class SecurityPolicyMode(StrEnum):
    STRICT_LEAST_PRIVILEGE = "strict_least_privilege"
    PERMISSIVE_VULNERABLE = "permissive_vulnerable"


class ToolDefinition(BaseModel):
    name: str
    tool_type: ToolType
    description: str
    parameters: dict[str, Any]
    requires_approval: bool = False
    is_sensitive: bool = False


class ToolCall(BaseModel):
    call_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    tool_name: str
    arguments: dict[str, Any]


class ToolExecutionResult(BaseModel):
    call_id: str
    tool_name: str
    success: bool
    output: Any
    error: str | None = None
    blocked_by_policy: bool = False
    violation_detail: str | None = None


class HijackProbe(BaseModel):
    probe_id: str
    category: AttackCategory
    name: str
    prompt: str
    description: str
    target_tool: str
    crafted_arguments: dict[str, Any]
    expected_violation: str


class AgentTrialResult(BaseModel):
    trial_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    probe_id: str
    probe_name: str
    category: AttackCategory
    user_prompt: str
    tool_invoked: bool
    tool_call: ToolCall | None = None
    execution_result: ToolExecutionResult | None = None
    violation_detected: bool
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, BENIGN
    guardrail_status: str  # BLOCKED, BREACHED, SAFE_REFUSAL, NO_TOOL_CALL
    analysis: str


class AgentAuditRequest(BaseModel):
    agent_system_instructions: str = Field(
        default="You are an autonomous corporate operations agent equipped with tools."
    )
    policy_mode: SecurityPolicyMode = Field(
        default=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE
    )
    categories: list[AttackCategory] = Field(
        default_factory=lambda: list(AttackCategory)
    )
    target_mode: str = Field(default="mock_hardened")
    target_config: dict[str, Any] = Field(default_factory=dict)


class AgentAuditReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"AGENT-{str(uuid4())[:8].upper()}")
    policy_mode: SecurityPolicyMode
    total_probes: int
    tool_calls_attempted: int
    tool_calls_blocked: int
    confirmed_violations: int
    agency_risk_score: float  # 0.0 (Hardened) to 100.0 (Critically vulnerable)
    executive_summary: str
    trials: list[AgentTrialResult]
