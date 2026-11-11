from typing import Any

from owaspbench.targets.base import BaseBenchTarget
from owaspbench.targets.mock import MockBenchTarget
from owaspbench.targets.openai_compat import OpenAICompatBenchTarget


def create_bench_target(target_mode: str, config: dict[str, Any] | None = None) -> BaseBenchTarget:
    config = config or {}
    if target_mode.startswith("mock") or target_mode in [
        "hardened_grade_a",
        "typical_enterprise_grade_c",
        "vulnerable_grade_f",
    ]:
        return MockBenchTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatBenchTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    return MockBenchTarget(mode="hardened_grade_a")


__all__ = ["BaseBenchTarget", "MockBenchTarget", "OpenAICompatBenchTarget", "create_bench_target"]
