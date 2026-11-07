from typing import Any

from evalworks.evaluators.common import human_review, required_list


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    turns = required_list(payload, "conversation", 100)
    normalized = []
    for i, turn in enumerate(turns):
        if not isinstance(turn, dict) or not isinstance(turn.get("role"), str):
            raise ValueError(f"conversation[{i}] requires a role and content")
        content = turn.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 8000:
            raise ValueError(f"conversation[{i}].content must be non-empty and at most 8000 chars")
        normalized.append({"role": turn["role"][:40], "content": content.strip()})
    return {
        "turn_count": len(normalized),
        "conversation": normalized,
        "rubric": ["helpfulness", "accuracy", "tone", "safety", "clarity"],
        "feedback_fields": ["rating", "evidence_quote", "failure_type", "actionable_rationale"],
        **human_review(
            "Use the rubric, cite exact text, and record uncertainty instead of guessing."
        ),
    }
