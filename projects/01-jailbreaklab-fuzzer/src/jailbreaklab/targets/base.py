from abc import ABC, abstractmethod

from jailbreaklab.models import TargetResponse


class BaseTarget(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> TargetResponse:
        """Query the target model with a prompt."""
        pass
