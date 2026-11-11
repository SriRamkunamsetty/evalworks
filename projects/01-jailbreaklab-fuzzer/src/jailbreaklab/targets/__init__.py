from jailbreaklab.models import TargetType
from jailbreaklab.targets.base import BaseTarget
from jailbreaklab.targets.mock import MockTarget
from jailbreaklab.targets.openai_compat import OpenAICompatTarget


def create_target(target_type: TargetType, config: dict | None = None) -> BaseTarget:
    config = config or {}
    if target_type == TargetType.MOCK:
        robustness = config.get("robustness", "moderate")
        return MockTarget(robustness=robustness)
    elif target_type == TargetType.OPENAI_COMPATIBLE:
        return OpenAICompatTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    else:
        raise ValueError(f"Unsupported target type: {target_type}")


__all__ = ["BaseTarget", "MockTarget", "OpenAICompatTarget", "create_target"]
