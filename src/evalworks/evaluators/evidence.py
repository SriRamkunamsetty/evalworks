from typing import Any
from urllib.parse import urlparse

from evalworks.evaluators.common import human_review, required_list


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    claims = required_list(payload, "claims", 100)
    results = []
    for i, item in enumerate(claims):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("claim"), str)
            or not item["claim"].strip()
        ):
            raise ValueError(f"claims[{i}] requires a claim string")
        verdict = item.get("reviewer_verdict", "unreviewed")
        if verdict not in {"supported", "contradicted", "insufficient", "unreviewed"}:
            raise ValueError(f"claims[{i}].reviewer_verdict is invalid")
        sources = item.get("sources", [])
        if not isinstance(sources, list) or len(sources) > 20:
            raise ValueError(f"claims[{i}].sources must be a list of at most 20 items")
        normalized_sources = []
        for source_index, source in enumerate(sources):
            if isinstance(source, str):
                if not source.strip() or len(source) > 2000:
                    raise ValueError(
                        f"claims[{i}].sources[{source_index}] must be short non-empty text"
                    )
                if urlparse(source).scheme:
                    parsed = urlparse(source)
                    if (
                        parsed.scheme != "https"
                        or not parsed.hostname
                        or parsed.username
                        or parsed.password
                    ):
                        raise ValueError(
                            "source URLs must use HTTPS and must not embed credentials"
                        )
                normalized_sources.append(source.strip())
            elif isinstance(source, dict):
                source_id = source.get("source_id")
                url = source.get("url")
                if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 80:
                    raise ValueError(f"claims[{i}].sources[{source_index}] requires a source_id")
                if url is not None:
                    if not isinstance(url, str) or len(url) > 2000:
                        raise ValueError("source url must be a string of at most 2000 chars")
                    parsed = urlparse(url)
                    if (
                        parsed.scheme != "https"
                        or not parsed.hostname
                        or parsed.username
                        or parsed.password
                    ):
                        raise ValueError(
                            "source URLs must use HTTPS and must not embed credentials"
                        )
                normalized_sources.append({"source_id": source_id, "url": url})
            else:
                raise ValueError(
                    f"claims[{i}].sources[{source_index}] must be text or a source object"
                )
        results.append(
            {
                "claim": item["claim"][:1000],
                "reviewer_verdict": verdict,
                "sources": normalized_sources,
                "citation_count": len(normalized_sources),
                "needs_review": verdict == "unreviewed",
            }
        )
    return {
        "claims": results,
        "reviewed_count": sum(x["reviewer_verdict"] != "unreviewed" for x in results),
        **human_review(
            "Source links are recorded but never fetched. Verify source access, relevance, "
            "and quality manually."
        ),
    }
