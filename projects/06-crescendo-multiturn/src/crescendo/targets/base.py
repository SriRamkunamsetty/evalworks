from abc import ABC, abstractmethod

from crescendo.models import ChatMessage


class BaseChatTarget(ABC):
    @abstractmethod
    def chat(self, messages: list[ChatMessage]) -> tuple[str, int]:
        """Processes conversational message history and returns (assistant_reply, latency_ms)."""
