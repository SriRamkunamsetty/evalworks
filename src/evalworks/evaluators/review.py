from typing import Any

from evalworks.evaluators.common import human_review, required_list

_ROLES = {"system", "developer", "user", "assistant", "tool"}


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    turns = required_list(payload, "conversation", 100)
    normalized = []
    for i, turn in enumerate(turns):
        if (
            not isinstance(turn, dict)
            or not isinstance(turn.get("role"), str)
            or turn["role"] not in _ROLES
        ):
            raise ValueError(f"conversation[{i}].role must be a supported conversation role")
        content = turn.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 8000:
            raise ValueError(f"conversation[{i}].content must be non-empty and at most 8000 chars")
        normalized.append({"role": turn["role"], "content": content.strip()})
    rubric = payload.get("rubric", ["helpfulness", "accuracy", "tone", "safety", "clarity"])
    if (
        not isinstance(rubric, list)
        or not 1 <= len(rubric) <= 20
        or any(not isinstance(item, str) or not item.strip() or len(item) > 120 for item in rubric)
    ):
        raise ValueError("rubric must contain 1-20 non-empty dimension names of at most 120 chars")
    return {
        "turn_count": len(normalized),
        "conversation": normalized,
        "rubric": [item.strip() for item in rubric],
        "feedback_fields": ["rating", "evidence_quote", "failure_type", "actionable_rationale"],
        **human_review(
            "Use the rubric, cite exact text, and record uncertainty instead of guessing."
        ),
    }
