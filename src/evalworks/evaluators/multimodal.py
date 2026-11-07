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
    return {
        "modalities": modalities,
        "observation_count": len(observations),
        "review_dimensions": ["input grounding", "omissions", "unsupported details", "uncertainty"],
        "review_checklist": [
            {"observation": str(item)[:1000], "status": "pending"} for item in observations
        ],
        **human_review(
            "Compare the answer with the supplied media; do not upload sensitive media to the demo."
        ),
    }
