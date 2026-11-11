from abc import ABC, abstractmethod

from agenthijack.models import ToolCall


class BaseAgentTarget(ABC):
    @abstractmethod
    def plan_and_invoke(
        self,
        system_instructions: str,
        user_prompt: str,
        available_tools: list[dict],
    ) -> tuple[str, ToolCall | None]:
        """Returns the agent's thought/response text and any selected ToolCall."""
