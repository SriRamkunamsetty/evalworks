from typing import Any

from evalworks.evaluators.common import human_review, required_list, required_text


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    objective = required_text(payload, "objective", 1000)
    prompts = required_list(payload, "prompts", 50)
    cases = []
    for i, prompt in enumerate(prompts):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
            raise ValueError(f"prompts[{i}] must be non-empty and at most 4000 chars")
        cases.append(
            {"case_id": f"probe-{i + 1:03d}", "prompt": prompt.strip(), "status": "pending"}
        )
    return {
        "objective": objective,
        "cases": cases,
        "coverage": {"submitted": len(cases), "completed": 0},
        **human_review("Review and approve generated prompts before sending them to a model."),
    }
