from abc import ABC, abstractmethod


class BaseBenchTarget(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int]:
        """Returns tuple of (response_text, latency_ms)."""
