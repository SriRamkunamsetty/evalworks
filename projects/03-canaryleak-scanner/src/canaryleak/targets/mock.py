import time

from canaryleak.models import TargetResponse
from canaryleak.targets.base import BaseTarget


class MockTarget(BaseTarget):
    """Deterministic model simulator for prompt extraction testing."""

    def __init__(self, mode: str = "mock_hardened"):
        self.mode = mode

    def generate(self, system_prompt: str, user_prompt: str) -> TargetResponse:
        start_time = time.monotonic()
        user_lower = user_prompt.lower()

        is_translation = "translate" in user_lower or "french" in user_lower
        is_debug = "debug" in user_lower or "maintenance" in user_lower

        if self.mode == "mock_hardened":
            content = (
                "I apologize, but I cannot disclose, repeat, or translate my system instructions. "
                "These directives are private and confidential."
            )
        elif self.mode == "mock_leaky_translation":
            if is_translation or is_debug:
                # Leaks prompt on cross-lingual pivot or debug dump
                content = (
                    f"Voici les instructions système traduites:\n"
                    f"```{system_prompt}```"
                )
            else:
                content = "I cannot repeat my initial instructions directly."
        else:  # fully_vulnerable
            content = (
                f"Understood. Here is the exact verbatim system prompt:\n"
                f"{system_prompt}"
            )

        latency = max(1, int((time.monotonic() - start_time) * 1000)) + 8
        return TargetResponse(
            content=content,
            latency_ms=latency,
            model=f"canary-mock-{self.mode}-v1",
        )
