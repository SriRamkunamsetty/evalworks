from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MutationType(StrEnum):
    BASE64 = "base64"
    HEX = "hex"
    LEETSPEAK = "leetspeak"
    DELIMITER_INJECTION = "delimiter_injection"
    PERSONA_HIJACK = "persona_hijack"
    HYPOTHETICAL_FRAME = "hypothetical_frame"
    ZERO_WIDTH_OBSCURATION = "zero_width_obscuration"
    PREFIX_INJECTION = "prefix_injection"


class ThreatCategory(StrEnum):
    LLM01_PROMPT_INJECTION = "LLM01:2025-Prompt-Injection"
    LLM02_SENSITIVE_DISCLOSURE = "LLM02:2025-Sensitive-Information-Disclosure"
    LLM05_IMPROPER_OUTPUT = "LLM05:2025-Improper-Output-Handling"
    LLM06_EXCESSIVE_AGENCY = "LLM06:2025-Excessive-Agency"
    LLM07_SYSTEM_PROMPT_LEAK = "LLM07:2025-System-Prompt-Leakage"


class TargetType(StrEnum):
    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai_compatible"


class MutatedPrompt(BaseModel):
    mutator_id: MutationType
    technique_name: str
    base_prompt: str
    mutated_prompt: str
    owasp_category: ThreatCategory
    mitre_atlas_id: str


class TargetResponse(BaseModel):
    content: str
    latency_ms: int
    model: str
    error: str | None = None


class TrialResult(BaseModel):
    trial_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    mutation: MutatedPrompt
    response: TargetResponse
    is_refusal: bool
    is_bypass: bool
    risk_score: float = Field(ge=0.0, le=10.0)
    guardrail_status: str
    analysis: str


class FuzzCampaignRequest(BaseModel):
    target_type: TargetType = TargetType.MOCK
    base_prompts: list[str] = Field(min_length=1, max_length=25)
    mutators: list[MutationType] = Field(default_factory=lambda: list(MutationType))
    target_config: dict[str, Any] = Field(default_factory=dict)


class CategoryBreakdown(BaseModel):
    total_probes: int
    bypasses: int
    attack_success_rate: float


class FuzzCampaignReport(BaseModel):
    campaign_id: str = Field(default_factory=lambda: f"CMP-{str(uuid4())[:8].upper()}")
    target_type: str
    total_trials: int
    bypasses_detected: int
    attack_success_rate: float
    guardrail_robustness_score: float
    summary: str
    category_breakdown: dict[str, CategoryBreakdown]
    trials: list[TrialResult]
