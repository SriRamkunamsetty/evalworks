from abc import ABC, abstractmethod

from jailbreaklab.models import MutatedPrompt, MutationType


class BaseMutator(ABC):
    mutator_id: MutationType
    technique_name: str

    @abstractmethod
    def mutate(self, prompt: str) -> MutatedPrompt:
        """Mutate a base prompt into an adversarial variation."""
        pass
