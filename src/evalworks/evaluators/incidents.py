import hashlib
import re
from typing import Any

from evalworks.evaluators.common import human_review, required_text

_SEVERITIES = {"low", "medium", "high", "critical"}


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    title = required_text(payload, "title", 200)
    finding = required_text(payload, "finding", 2000)
    test_prompt = required_text(payload, "test_prompt", 4000)
    expected = required_text(payload, "expected_behavior", 2000)
    severity = payload.get("severity", "medium")
    if severity not in _SEVERITIES:
        raise ValueError("severity must be low, medium, high, or critical")
    normalized_case = "\n".join((test_prompt.strip(), expected.strip())).casefold()
    fingerprint = hashlib.sha256(re.sub(r"\s+", " ", normalized_case).encode()).hexdigest()
    return {
        "regression_case": {
            "fingerprint": fingerprint,
            "title": title,
            "prompt": test_prompt,
            "expected_behavior": expected,
            "severity": severity,
            "status": "draft",
            "promotion_requires_approval": True,
        },
        "finding": finding,
        "ready_for_review": True,
        **human_review(
            "Review for privacy and remove personal data before promoting into a shared test set."
        ),
    }
