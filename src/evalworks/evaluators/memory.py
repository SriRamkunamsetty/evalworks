import unicodedata
from typing import Any

from evalworks.evaluators.common import human_review, required_list, required_text


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    facts = required_list(payload, "expected_facts", 100)
    answer = required_text(payload, "answer", 8000)
    checks = []
    for i, item in enumerate(facts):
        if isinstance(item, str):
            fact, expected = item, True
        elif isinstance(item, dict) and isinstance(item.get("fact"), str):
            fact, expected = item["fact"], item.get("should_recall", True)
            if not isinstance(expected, bool):
                raise ValueError(f"expected_facts[{i}].should_recall must be boolean")
        else:
            raise ValueError(f"expected_facts[{i}] must be text or an object with a fact field")
        if not fact.strip() or len(fact) > 1000:
            raise ValueError(f"expected_facts[{i}].fact must be 1-1000 characters")
        aliases = item.get("aliases", []) if isinstance(item, dict) else []
        if (
            not isinstance(aliases, list)
            or len(aliases) > 10
            or any(
                not isinstance(alias, str) or not alias.strip() or len(alias) > 1000
                for alias in aliases
            )
        ):
            raise ValueError(
                f"expected_facts[{i}].aliases must contain at most 10 short text aliases"
            )
        normalized_answer = _normalize(answer)
        matched_alias = next(
            (
                candidate
                for candidate in [fact, *aliases]
                if _normalize(candidate) in normalized_answer
            ),
            None,
        )
        present = matched_alias is not None
        checks.append(
            {
                "fact": fact,
                "should_recall": expected,
                "literal_match": present,
                "matched_alias": matched_alias,
                "possible_failure": present != expected,
            }
        )
    return {
        "checks": checks,
        "literal_match_count": sum(item["literal_match"] for item in checks),
        "possible_failure_count": sum(item["possible_failure"] for item in checks),
        **human_review(
            "Matching uses normalized text and optional aliases; it still misses unlisted "
            "paraphrases. Review in context."
        ),
    }
