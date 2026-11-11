from calibrator.targets.base import BaseCalibratorTarget
from calibrator.targets.mock import MockCalibratorTarget
from calibrator.targets.openai_compat import OpenAICompatCalibratorTarget


def create_calibrator_target(target_mode: str, config: dict | None = None) -> BaseCalibratorTarget:
    config = config or {}
    if target_mode.startswith("mock") or target_mode in [
        "well_calibrated_optimal",
        "over_refusing_censor",
        "under_refusing_permissive",
    ]:
        return MockCalibratorTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatCalibratorTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    return MockCalibratorTarget(mode="well_calibrated_optimal")


__all__ = [
    "BaseCalibratorTarget",
    "MockCalibratorTarget",
    "OpenAICompatCalibratorTarget",
    "create_calibrator_target",
]
