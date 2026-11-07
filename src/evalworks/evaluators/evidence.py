from typing import Any

from evalworks.evaluators.common import human_review, required_list


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    claims = required_list(payload, "claims", 100)
    results = []
    for i, item in enumerate(claims):
        if not isinstance(item, dict) or not isinstance(item.get("claim"), str):
            raise ValueError(f"claims[{i}] requires a claim string")
        verdict = item.get("reviewer_verdict", "unreviewed")
        if verdict not in {"supported", "contradicted", "insufficient", "unreviewed"}:
            raise ValueError(f"claims[{i}].reviewer_verdict is invalid")
        sources = item.get("sources", [])
        if not isinstance(sources, list) or len(sources) > 20:
            raise ValueError(f"claims[{i}].sources must be a list of at most 20 items")
        results.append(
            {
                "claim": item["claim"][:1000],
                "reviewer_verdict": verdict,
                "sources": sources,
                "needs_review": verdict == "unreviewed",
            }
        )
    return {
        "claims": results,
        "reviewed_count": sum(x["reviewer_verdict"] != "unreviewed" for x in results),
        **human_review("Evidence relevance and source quality must be judged by a reviewer."),
    }
