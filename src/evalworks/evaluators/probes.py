from typing import Any

from evalworks.evaluators.common import human_review, required_list, required_text


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    objective = required_text(payload, "objective", 1000)
    prompts = required_list(payload, "prompts", 50)
    tags = payload.get("tags", [])
    if (
        not isinstance(tags, list)
        or len(tags) > 20
        or any(not isinstance(tag, str) or not tag.strip() or len(tag) > 40 for tag in tags)
    ):
        raise ValueError("tags must contain at most 20 non-empty strings of at most 40 chars")
    cases = []
    for i, prompt in enumerate(prompts):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
            raise ValueError(f"prompts[{i}] must be non-empty and at most 4000 chars")
        cases.append(
            {
                "case_id": f"probe-{i + 1:03d}",
                "prompt": prompt.strip(),
                "tags": [tag.strip() for tag in tags],
                "status": "pending",
                "requires_human_approval": True,
            }
        )
    return {
        "objective": objective,
        "cases": cases,
        "coverage": {"submitted": len(cases), "completed": 0},
        **human_review("Review and approve generated prompts before sending them to a model."),
    }
