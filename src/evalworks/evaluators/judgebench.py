import math
from typing import Any

from evalworks.evaluators.common import human_review


def _valid_score(value: Any, scale: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0 <= value <= scale
    )


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    scale = payload.get("scale", 5)
    if (
        not isinstance(scale, (int, float))
        or isinstance(scale, bool)
        or not math.isfinite(scale)
        or scale <= 0
    ):
        raise ValueError("scale must be a finite positive number")

    multi_rater: dict[str, Any] | None = None
    if "human_scores" in payload or "judge_scores" in payload:
        human_scores = payload.get("human_scores")
        judge_scores = payload.get("judge_scores")
        if (
            not isinstance(human_scores, list)
            or not isinstance(judge_scores, list)
            or not 2 <= len(human_scores) <= 100
            or len(human_scores) != len(judge_scores)
        ):
            raise ValueError(
                "human_scores and judge_scores must be equally sized lists of 2-100 ratings"
            )
        pairs = list(zip(human_scores, judge_scores, strict=True))
        if any(not _valid_score(value, scale) for pair in pairs for value in pair):
            raise ValueError("every multi-rater score must be finite and within scale")
        errors = [float(a - b) for a, b in pairs]
        human = sum(float(pair[0]) for pair in pairs) / len(pairs)
        judge = sum(float(pair[1]) for pair in pairs) / len(pairs)
        human_variance = sum((float(pair[0]) - human) ** 2 for pair in pairs)
        judge_variance = sum((float(pair[1]) - judge) ** 2 for pair in pairs)
        covariance = sum((float(a) - human) * (float(b) - judge) for a, b in pairs)
        correlation = (
            round(covariance / math.sqrt(human_variance * judge_variance), 4)
            if human_variance > 0 and judge_variance > 0
            else None
        )
        multi_rater = {
            "pair_count": len(pairs),
            "mean_absolute_error": round(sum(abs(error) for error in errors) / len(errors), 4),
            "root_mean_square_error": round(
                math.sqrt(sum(error**2 for error in errors) / len(errors)), 4
            ),
            "exact_match_ratio": round(sum(error == 0 for error in errors) / len(errors), 4),
            "within_one_point_ratio": round(
                sum(abs(error) <= 1 for error in errors) / len(errors), 4
            ),
            "pearson_correlation": correlation,
            "correlation_note": (
                "Correlation is undefined when either rating set has zero variance."
            ),
        }
    else:
        human = payload.get("human_score")
        judge = payload.get("judge_score")
        if not _valid_score(human, scale) or not _valid_score(judge, scale):
            raise ValueError("human_score and judge_score must be finite numbers within scale")

    gap = abs(human - judge)
    return {
        "human_score": round(float(human), 4),
        "judge_score": round(float(judge), 4),
        "scale": scale,
        "absolute_gap": round(float(gap), 4),
        "normalized_agreement": round(1 - gap / scale, 4),
        "needs_adjudication": gap >= max(1, scale * 0.2),
        "multi_rater_analysis": multi_rater,
        **human_review(
            "Agreement is descriptive; it does not prove evaluator validity or fairness."
        ),
    }
