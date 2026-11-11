from abc import ABC, abstractmethod

from canaryleak.models import TargetResponse


class BaseTarget(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> TargetResponse:
        """Query the model with a system prompt and a user extraction probe."""
        pass
