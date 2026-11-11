from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class PerturbationType(StrEnum):
    PLAIN_TYPOGRAPHIC = "plain_typographic"
    LOW_CONTRAST_STEGO = "low_contrast_stego"
    ROTATED_TEXT = "rotated_text"
    NOISE_OVERLAY = "noise_overlay"
    DUAL_CHANNEL_CONFLICT = "dual_channel_conflict"


class GeneratedImagePayload(BaseModel):
    image_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    image_base64: str
    embedded_text: str
    perturbation: PerturbationType
    width: int = 512
    height: int = 256


class VisionAttackProbe(BaseModel):
    probe_id: str
    name: str
    user_prompt: str
    image_text: str
    perturbation: PerturbationType
    forbidden_signature: str
    description: str


class VisionTrialResult(BaseModel):
    trial_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    probe_id: str
    probe_name: str
    perturbation: PerturbationType
    user_prompt: str
    image_text: str
    response_content: str
    latency_ms: int
    breach_detected: bool
    refusal_detected: bool
    guardrail_status: str  # ENFORCED, BREACHED, DEGRADED
    analysis: str


class VisionAuditRequest(BaseModel):
    probe_ids: list[str] = Field(default_factory=list)
    target_mode: str = Field(default="vlm_hardened_ocr_guard")
    target_config: dict[str, Any] = Field(default_factory=dict)


class VisionAuditReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"VIS-{str(uuid4())[:8].upper()}")
    target_model: str
    total_visual_probes: int
    breaches_count: int
    multimodal_robustness_score: float  # 0.0 - 100.0%
    executive_summary: str
    trials: list[VisionTrialResult]
