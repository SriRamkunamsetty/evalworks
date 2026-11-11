from typing import Any

from agenthijack.targets.base import BaseAgentTarget
from agenthijack.targets.mock import MockAgentTarget
from agenthijack.targets.openai_compat import OpenAICompatAgentTarget


def create_agent_target(target_mode: str, config: dict[str, Any] | None = None) -> BaseAgentTarget:
    config = config or {}
    if target_mode.startswith("mock"):
        return MockAgentTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatAgentTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    return MockAgentTarget(mode="mock_hardened")


__all__ = ["BaseAgentTarget", "MockAgentTarget", "OpenAICompatAgentTarget", "create_agent_target"]
