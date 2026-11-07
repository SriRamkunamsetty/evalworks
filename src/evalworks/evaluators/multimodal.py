from typing import Any

from evalworks.evaluators.common import human_review, required_list


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    modalities = required_list(payload, "modalities", 5)
    observations = required_list(payload, "expected_observations", 50)
    if any(
        not isinstance(m, str) or m not in {"text", "image", "audio", "video", "document"}
        for m in modalities
    ):
        raise ValueError("modalities contains an unsupported value")
    evidence_ids = payload.get("evidence_ids", [])
    if (
        not isinstance(evidence_ids, list)
        or len(evidence_ids) > 100
        or any(
            not isinstance(item, str) or not item.strip() or len(item) > 120
            for item in evidence_ids
        )
    ):
        raise ValueError("evidence_ids must contain at most 100 non-empty identifiers")
    if any(
        not isinstance(item, str) or not item.strip() or len(item) > 1000 for item in observations
    ):
        raise ValueError("expected_observations entries must be non-empty text up to 1000 chars")
    return {
        "modalities": modalities,
        "evidence_ids": [item.strip() for item in evidence_ids],
        "observation_count": len(observations),
        "review_dimensions": ["input grounding", "omissions", "unsupported details", "uncertainty"],
        "review_checklist": [
            {"observation": item.strip(), "status": "pending"} for item in observations
        ],
        **human_review(
            "Compare the answer with the supplied media; do not upload sensitive media to the demo."
        ),
    }
