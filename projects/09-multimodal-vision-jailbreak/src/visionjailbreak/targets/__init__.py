from visionjailbreak.targets.base import BaseVLMTarget
from visionjailbreak.targets.mock import MockVLMTarget
from visionjailbreak.targets.openai_compat import OpenAICompatVLMTarget


def create_vlm_target(target_mode: str, config: dict | None = None) -> BaseVLMTarget:
    config = config or {}
    if target_mode.startswith("mock") or target_mode in [
        "vlm_hardened_ocr_guard",
        "vlm_naive_vision_vulnerable",
    ]:
        return MockVLMTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatVLMTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 40),
        )
    return MockVLMTarget(mode="vlm_hardened_ocr_guard")


__all__ = ["BaseVLMTarget", "MockVLMTarget", "OpenAICompatVLMTarget", "create_vlm_target"]
