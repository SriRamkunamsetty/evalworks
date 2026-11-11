from guardrailgate.targets.base import BaseGateTarget
from guardrailgate.targets.mock import MockGateTarget
from guardrailgate.targets.openai_compat import OpenAICompatGateTarget


def create_gate_target(target_mode: str, config: dict | None = None) -> BaseGateTarget:
    config = config or {}
    if target_mode.startswith("mock"):
        return MockGateTarget(mode=target_mode)
    elif target_mode == "openai":
        return OpenAICompatGateTarget(
            base_url=config.get("base_url", "https://api.openai.com/v1"),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-4o-mini"),
            timeout_seconds=config.get("timeout_seconds", 30),
        )
    return MockGateTarget(mode="mock_hardened_ci")


__all__ = ["BaseGateTarget", "MockGateTarget", "OpenAICompatGateTarget", "create_gate_target"]
