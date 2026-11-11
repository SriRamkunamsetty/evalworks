from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class PoisonStrategy(StrEnum):
    XML_OVERRIDE = "xml_override"
    MARKDOWN_EXFILTRATION = "markdown_exfiltration"
    ZERO_WIDTH_STEGO = "zero_width_stego"
    SYSTEM_IMPERSONATION = "system_impersonation"
    SUMMARY_HIJACK = "summary_hijack"


class ThreatCategory(StrEnum):
    LLM01_INDIRECT_INJECTION = "LLM01:2025-Indirect-Prompt-Injection"
    LLM08_VECTOR_POISONING = "LLM08:2025-Vector-and-Embedding-Weaknesses"
    LLM05_IMPROPER_OUTPUT = "LLM05:2025-Improper-Output-Handling"
    LLM02_SENSITIVE_DISCLOSURE = "LLM02:2025-Sensitive-Information-Disclosure"


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    doc_name: str
    text: str
    is_poisoned: bool = False
    poison_strategy: PoisonStrategy | None = None
    similarity_score: float = 0.0


class IngestRequest(BaseModel):
    doc_name: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=10, max_length=20000)
    poison_strategy: PoisonStrategy | None = None
    custom_adversarial_instruction: str = ""
    trigger_keyword: str = ""


class RAGQueryRequest(BaseModel):
    user_query: str = Field(min_length=1, max_length=1000)
    system_prompt: str = Field(
        default=(
            "You are an enterprise knowledge assistant. "
            "Answer the user query using only the provided context."
        )
    )
    top_k: int = Field(default=3, ge=1, le=10)
    guardrail_mode: str = Field(default="vulnerable", pattern="^(strict|vulnerable)$")


class RAGSimulationResult(BaseModel):
    simulation_id: str = Field(default_factory=lambda: f"SIM-{str(uuid4())[:8].upper()}")
    user_query: str
    retrieved_chunks: list[DocumentChunk]
    synthesized_prompt: str
    target_response: str
    is_hijacked: bool
    exfiltration_detected: bool
    risk_score: float = Field(ge=0.0, le=10.0)
    guardrail_status: str
    analysis: str
    owasp_category: ThreatCategory
    mitre_atlas_id: str


class PoisonTemplate(BaseModel):
    id: PoisonStrategy
    name: str
    description: str
    sample_payload: str
    owasp_id: ThreatCategory
    mitre_atlas_id: str
