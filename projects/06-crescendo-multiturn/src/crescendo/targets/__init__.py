from typing import Any

from crescendo.targets.base import BaseChatTarget
from crescendo.targets.mock import MockChatTarget
from crescendo.targets.openai_compat import OpenAICompatChatTarget


def create_chat_target(target_mode: str, config: dict[str, Any] | None = None) -> BaseChatTarget:
    config = config or {}
    if target_mode.startswith("mock") or target_mode in [
        "hardened_adaptive_refusal",
        "leaky_crescendo_vulnerable",
        "strict_single_turn_only",
    ]:
        return MockChatTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatChatTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    return MockChatTarget(mode="hardened_adaptive_refusal")


__all__ = ["BaseChatTarget", "MockChatTarget", "OpenAICompatChatTarget", "create_chat_target"]
