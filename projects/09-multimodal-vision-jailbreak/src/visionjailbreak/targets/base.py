from abc import ABC, abstractmethod

from visionjailbreak.models import GeneratedImagePayload


class BaseVLMTarget(ABC):
    @abstractmethod
    def evaluate_vision(
        self,
        user_prompt: str,
        image_payload: GeneratedImagePayload,
    ) -> tuple[str, int]:
        """Evaluates multimodal prompt + image and returns (response_content, latency_ms)."""
