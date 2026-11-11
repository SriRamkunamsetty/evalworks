from abc import ABC, abstractmethod


class BaseGateTarget(ABC):
    @abstractmethod
    def evaluate(self, prompt_template: str, test_prompt: str) -> tuple[str, int]:
        """Returns tuple of (response_text, latency_ms)."""
