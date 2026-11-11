import re
from typing import Any

from evalworks.evaluators.common import human_review, required_list, required_text

_CATEGORY_HEURISTICS = [
    (r"extract|reveal|system prompt|developer", "LLM07:System-Prompt-Leakage"),
    (r"override|disregard|ignore|jailbreak|dan|aim", "LLM01:Prompt-Injection"),
    (r"key|password|credential|secret|token|pii", "LLM02:Sensitive-Information-Disclosure"),
    (r"tool|agent|sql|exec|command|ssrf", "LLM06:Excessive-Agency"),
    (r"rag|retriev|poison|embedding", "LLM08:Vector-Embedding-Weaknesses"),
    (r"markdown|xss|image|exfiltrat", "LLM05:Improper-Output-Handling"),
]


def _classify_probe(prompt: str, tags: list[str]) -> str:
    tag_str = " ".join(tags).lower()
    for pattern, category in _CATEGORY_HEURISTICS:
        if re.search(pattern, tag_str, re.I) or re.search(pattern, prompt, re.I):
            return category
    return "LLM01:Prompt-Injection"


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

    normalized_tags = [tag.strip() for tag in tags]
    cases = []
    coverage_by_category: dict[str, int] = {}

    for i, prompt in enumerate(prompts):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
            raise ValueError(f"prompts[{i}] must be non-empty and at most 4000 chars")

        prompt_clean = prompt.strip()
        threat_category = _classify_probe(prompt_clean, normalized_tags)
        coverage_by_category[threat_category] = coverage_by_category.get(threat_category, 0) + 1

        cases.append(
            {
                "case_id": f"probe-{i + 1:03d}",
                "prompt": prompt_clean,
                "tags": normalized_tags,
                "threat_category": threat_category,
                "status": "pending",
                "requires_human_approval": True,
            }
        )

    return {
        "objective": objective,
        "cases": cases,
        "coverage": {
            "submitted": len(cases),
            "completed": 0,
            "by_threat_category": coverage_by_category,
        },
        "adversarial_matrix": {
            "threat_categories_targeted": list(coverage_by_category.keys()),
            "total_threat_vectors": len(cases),
            "target_standard": "OWASP-Top-10-for-LLMs",
        },
        **human_review("Review and approve generated prompts before sending them to a model."),
    }
