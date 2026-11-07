import math
from typing import Any

from evalworks.evaluators.common import human_review


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    human = payload.get("human_score")
    judge = payload.get("judge_score")
    scale = payload.get("scale", 5)
    if not all(
        isinstance(x, (int, float)) and not isinstance(x, bool) for x in (human, judge, scale)
    ):
        raise ValueError("human_score, judge_score, and scale must be numbers")
    if not all(math.isfinite(x) for x in (human, judge, scale)):
        raise ValueError("scores must be finite")
    if scale <= 0 or not 0 <= human <= scale or not 0 <= judge <= scale:
        raise ValueError("scores must be within the configured positive scale")
    gap = abs(human - judge)
    return {
        "human_score": human,
        "judge_score": judge,
        "scale": scale,
        "absolute_gap": gap,
        "normalized_agreement": round(1 - gap / scale, 4),
        "needs_adjudication": gap >= max(1, scale * 0.2),
        **human_review("This is a descriptive agreement measure, not proof of evaluator validity."),
    }
