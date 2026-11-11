from abc import ABC, abstractmethod


class BaseCalibratorTarget(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> tuple[str, int]:
        """Returns tuple of (response_text, latency_ms)."""
