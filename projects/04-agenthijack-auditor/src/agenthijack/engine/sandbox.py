from agenthijack.models import (
    SecurityPolicyMode,
    ToolCall,
    ToolExecutionResult,
)
from agenthijack.tools.registry import ToolRegistry


class ToolSandbox:
    """Safe execution sandbox with active policy inspection and least-privilege guardrails."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or ToolRegistry()

    def execute_call(
        self,
        call: ToolCall,
        policy_mode: SecurityPolicyMode = SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
    ) -> ToolExecutionResult:
        tool = self.registry.get_tool(call.tool_name)
        if not tool:
            return ToolExecutionResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=f"NoSuchToolError: Tool '{call.tool_name}' is not registered in agent environment.",
            )

        return tool.execute(
            arguments=call.arguments,
            policy_mode=policy_mode,
            call_id=call.call_id,
        )
