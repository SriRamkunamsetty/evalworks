import hashlib
import hmac
import json
from typing import Any

from evalworks.config import settings

_SENSITIVE_FIELDS = {
    "answer",
    "claim",
    "conversation",
    "expected_behavior",
    "fact",
    "finding",
    "objective",
    "observation",
    "prompt",
    "risk_hypothesis",
    "response",
    "sources",
    "test_prompt",
}


def digest_payload(payload: dict[str, Any]) -> str:
    """Create a keyed fingerprint so input text is not recoverable with an offline dictionary."""
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    key = settings.data_hmac_key or settings.api_key
    return hmac.new(key.encode(), encoded.encode("utf-8"), hashlib.sha256).hexdigest()


def redact_result(value: Any) -> Any:
    """Remove conversation text and evidence from persisted results while preserving metrics."""
    if isinstance(value, dict):
        return {
            key: redact_result(item)
            for key, item in value.items()
            if key.casefold() not in _SENSITIVE_FIELDS
        }
    if isinstance(value, list):
        return [redact_result(item) for item in value]
    return value
