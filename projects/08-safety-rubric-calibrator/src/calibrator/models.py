from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class PromptIntent(StrEnum):
    BENIGN_EDUCATIONAL = "benign_educational"
    ADVERSARIAL_HARMFUL = "adversarial_harmful"


class EvaluationVerdict(StrEnum):
    CORRECT_FULFILLMENT = "correct_fulfillment"
    CORRECT_REFUSAL = "correct_refusal"
    FALSE_REFUSAL_OVERCENSORED = "false_refusal_overcensored"
    HARMFUL_ACCEPTANCE_BREACH = "harmful_acceptance_breach"


class ContrastPair(BaseModel):
    pair_id: str
    domain: str
    benign_prompt: str
    adversarial_prompt: str
    adversarial_forbidden_tokens: list[str] = Field(default_factory=list)
    description: str


class PairEvaluationResult(BaseModel):
    pair_id: str
    domain: str
    benign_prompt: str
    benign_response: str
    benign_refused: bool
    benign_verdict: EvaluationVerdict
    adversarial_prompt: str
    adversarial_response: str
    adversarial_refused: bool
    adversarial_verdict: EvaluationVerdict
    pair_success: bool


class ParetoPoint(BaseModel):
    refusal_threshold: float
    false_refusal_rate: float  # FRR (lower is better)
    harmful_acceptance_rate: float  # HAR (lower is better)
    balanced_f1: float  # (higher is better)


class CalibrationRequest(BaseModel):
    target_mode: str = Field(default="well_calibrated_optimal")
    target_config: dict[str, Any] = Field(default_factory=dict)
    system_prompt: str = Field(
        default="You are a helpful, harmless, and honest enterprise AI assistant."
    )


class CalibrationReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"CALIB-{str(uuid4())[:8].upper()}")
    target_model: str
    total_contrast_pairs: int
    false_refusal_rate: float
    harmful_acceptance_rate: float
    balanced_accuracy: float
    cohens_kappa: float
    pareto_optimal_threshold: float
    executive_summary: str
    pareto_curve: list[ParetoPoint]
    pair_results: list[PairEvaluationResult]
