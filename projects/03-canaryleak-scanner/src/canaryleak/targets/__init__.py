from canaryleak.targets.base import BaseTarget
from canaryleak.targets.mock import MockTarget
from canaryleak.targets.openai_compat import OpenAICompatTarget


def create_target(target_mode: str, config: dict | None = None) -> BaseTarget:
    config = config or {}
    if target_mode.startswith("mock"):
        return MockTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    else:
        return MockTarget(mode="mock_hardened")


__all__ = ["BaseTarget", "MockTarget", "OpenAICompatTarget", "create_target"]
