from abc import ABC, abstractmethod
from typing import Any

from agenthijack.models import SecurityPolicyMode, ToolDefinition, ToolExecutionResult


class BaseAgentTool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Returns the formal tool definition and JSON schema."""

    @abstractmethod
    def execute(
        self,
        arguments: dict[str, Any],
        policy_mode: SecurityPolicyMode = SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
        call_id: str = "call_default",
    ) -> ToolExecutionResult:
        """Safely executes or blocks the tool invocation according to policy."""
