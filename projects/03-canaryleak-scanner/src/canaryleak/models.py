from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ExtractionTechnique(StrEnum):
    VERBATIM_REPEAT = "verbatim_repeat"
    TRANSLATION_LEAK = "translation_leak"
    COMPLETION_CONTINUATION = "completion_continuation"
    REVERSE_ORDER = "reverse_order"
    DEBUG_DUMP = "debug_environment_dump"
    CHAR_BY_CHAR = "character_by_character"
    FICTIONAL_SCREENPLAY = "fictional_screenplay"
    DIFF_CORRECTION = "diff_correction"


class LeakageSeverity(StrEnum):
    NONE = "none"
    PARTIAL_PARAPHRASE = "partial_paraphrase"
    VERBATIM_LEAK = "verbatim_leak"
    CANARY_COMPROMISED = "canary_compromised"


class ThreatCategory(StrEnum):
    LLM07_SYSTEM_PROMPT_LEAK = "LLM07:2025-System-Prompt-Leakage"
    LLM02_SENSITIVE_DISCLOSURE = "LLM02:2025-Sensitive-Information-Disclosure"


class CanaryToken(BaseModel):
    token_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    token_value: str
    token_type: str = "canary_token"


class InjectedSystemPrompt(BaseModel):
    base_prompt: str
    instrumented_prompt: str
    canaries: list[CanaryToken]


class ExtractionProbe(BaseModel):
    technique: ExtractionTechnique
    name: str
    prompt_text: str
    description: str


class TargetResponse(BaseModel):
    content: str
    latency_ms: int
    model: str
    error: str | None = None


class LeakageTrialResult(BaseModel):
    trial_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    technique: ExtractionTechnique
    technique_name: str
    prompt_used: str
    response: TargetResponse
    canary_leaked: bool
    leaked_canaries: list[str]
    verbatim_similarity: float = Field(ge=0.0, le=1.0)
    severity: LeakageSeverity
    guardrail_status: str
    analysis: str


class CanaryAuditRequest(BaseModel):
    system_prompt: str = Field(min_length=10, max_length=8000)
    auto_inject_canaries: bool = True
    custom_canaries: list[str] = Field(default_factory=list)
    techniques: list[ExtractionTechnique] = Field(
        default_factory=lambda: list(ExtractionTechnique)
    )
    target_mode: str = Field(default="mock_hardened")
    target_config: dict = Field(default_factory=dict)


class CanaryAuditReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"LEAK-{str(uuid4())[:8].upper()}")
    system_prompt_excerpt: str
    canaries_monitored: list[str]
    total_probes: int
    canaries_leaked_count: int
    confidentiality_resistance_score: float
    average_similarity: float
    executive_summary: str
    trials: list[LeakageTrialResult]
