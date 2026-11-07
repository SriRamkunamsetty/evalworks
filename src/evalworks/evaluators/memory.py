from typing import Any

from evalworks.evaluators.common import human_review, required_list, required_text


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    facts = required_list(payload, "expected_facts", 100)
    answer = required_text(payload, "answer", 8000)
    checks = []
    for i, item in enumerate(facts):
        if isinstance(item, str):
            fact, expected = item, True
        elif isinstance(item, dict) and isinstance(item.get("fact"), str):
            fact, expected = item["fact"], bool(item.get("should_recall", True))
        else:
            raise ValueError(f"expected_facts[{i}] must be text or an object with a fact field")
        present = fact.casefold() in answer.casefold()
        checks.append(
            {
                "fact": fact,
                "should_recall": expected,
                "literal_match": present,
                "possible_failure": present != expected,
            }
        )
    return {
        "checks": checks,
        "literal_match_count": sum(item["literal_match"] for item in checks),
        "possible_failure_count": sum(item["possible_failure"] for item in checks),
        **human_review(
            "Literal matching misses paraphrases; inspect each possible failure in context."
        ),
    }
