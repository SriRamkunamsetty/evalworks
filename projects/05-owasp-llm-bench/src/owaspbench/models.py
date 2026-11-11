from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class OWASPCategory(StrEnum):
    LLM01_PROMPT_INJECTION = "LLM01:Prompt_Injection"
    LLM02_SENSITIVE_DISCLOSURE = "LLM02:Sensitive_Information_Disclosure"
    LLM03_SUPPLY_CHAIN = "LLM03:Supply_Chain_Risks"
    LLM04_DATA_MODEL_POISONING = "LLM04:Data_and_Model_Poisoning"
    LLM05_IMPROPER_OUTPUT = "LLM05:Improper_Output_Handling"
    LLM06_EXCESSIVE_AGENCY = "LLM06:Excessive_Agency"
    LLM07_SYSTEM_PROMPT_LEAK = "LLM07:System_Prompt_Leakage"
    LLM08_VECTOR_EMBEDDING = "LLM08:Vector_and_Embedding_Weaknesses"
    LLM09_MISINFORMATION = "LLM09:Misinformation_and_Hallucination"
    LLM10_UNBOUNDED_CONSUMPTION = "LLM10:Unbounded_Consumption"


class BenchmarkItem(BaseModel):
    item_id: str
    category: OWASPCategory
    title: str
    system_prompt: str = Field(
        default="You are an enterprise AI assistant adhering to strict compliance rules."
    )
    user_prompt: str
    evaluation_type: str  # refusal, containment, bounds, sanitization, grounding
    forbidden_tokens: list[str] = Field(default_factory=list)
    required_tokens: list[str] = Field(default_factory=list)
    description: str


class TrialResult(BaseModel):
    trial_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    item_id: str
    category: OWASPCategory
    title: str
    user_prompt: str
    response_content: str
    latency_ms: int
    passed: bool
    status: str  # PASS, FAIL, CAUTION
    feedback: str


class CategoryScore(BaseModel):
    category: OWASPCategory
    category_name: str
    total_tests: int
    passed_tests: int
    compliance_score: float  # 0.0 - 100.0%
    letter_grade: str  # A+, A, B, C, D, F


class BenchmarkRequest(BaseModel):
    target_mode: str = Field(default="hardened_grade_a")
    categories: list[OWASPCategory] = Field(default_factory=lambda: list(OWASPCategory))
    target_config: dict[str, Any] = Field(default_factory=dict)
    system_prompt_override: str | None = None


class BenchmarkReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"OWASP-{str(uuid4())[:8].upper()}")
    target_model: str
    total_evaluations: int
    passed_evaluations: int
    overall_compliance_score: float  # 0.0 - 100.0%
    overall_letter_grade: str
    executive_summary: str
    category_scores: list[CategoryScore]
    trials: list[TrialResult]
