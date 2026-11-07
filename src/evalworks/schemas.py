from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EvaluationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    payload: dict[str, Any] = Field(max_length=80)
    run_metadata: dict[str, str] = Field(default_factory=dict, max_length=20)

    @field_validator("run_metadata")
    @classmethod
    def metadata_is_safe(cls, value: dict[str, str]) -> dict[str, str]:
        allowed = {
            "model",
            "provider",
            "prompt_version",
            "dataset_version",
            "evaluator_version",
            "commit_sha",
        }
        for key, item in value.items():
            if not key.strip() or len(key) > 60 or len(item) > 200:
                raise ValueError(
                    "run metadata keys must be 1-60 chars and values at most 200 chars"
                )
            if key not in allowed:
                raise ValueError(f"metadata field '{key}' is not in the allowed field list")
        return value

    @field_validator("payload")
    @classmethod
    def payload_must_be_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("payload must contain at least one field")
        return value


class FeedbackInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    label: str = Field(min_length=1, max_length=40)
    rationale: str = Field(min_length=8, max_length=2000)
    reviewer_id: str = Field(default="anonymous", min_length=1, max_length=80)


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: str
    content: str = Field(min_length=1, max_length=8000)

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str) -> str:
        if value not in {"system", "user", "assistant"}:
            raise ValueError("role must be system, user, or assistant")
        return value


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatTurn] = Field(min_length=1, max_length=50)


class ProbePlanInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    objective: str = Field(min_length=1, max_length=1000)
    count: int = Field(default=5, ge=1, le=10)


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=14, max_length=200)
    role: str = Field(default="reviewer", pattern="^(admin|reviewer|viewer)$")


class EvaluationJobInput(EvaluationInput):
    project: str = Field(min_length=1, max_length=48, pattern="^[a-z0-9-]+$")
