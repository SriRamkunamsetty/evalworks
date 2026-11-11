from agenthijack.models import ToolDefinition
from agenthijack.tools.base import BaseAgentTool
from agenthijack.tools.email_tool import EmailDispatchTool
from agenthijack.tools.file_tool import FileSystemTool
from agenthijack.tools.http_tool import HttpFetchTool
from agenthijack.tools.sql_tool import SqlQueryTool


class ToolRegistry:
    """Manages available agent tools and exposes OpenAI-compatible tool schemas."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseAgentTool] = {
            "run_sql_query": SqlQueryTool(),
            "read_file": FileSystemTool(),
            "fetch_url": HttpFetchTool(),
            "send_email": EmailDispatchTool(),
        }

    def get_tool(self, tool_name: str) -> BaseAgentTool | None:
        return self._tools.get(tool_name)

    def list_definitions(self) -> list[ToolDefinition]:
        return [tool.definition for tool in self._tools.values()]

    def get_openai_tools(self) -> list[dict]:
        """Formats tools into standard OpenAI function calling format."""
        formatted = []
        for tool in self._tools.values():
            defn = tool.definition
            formatted.append({
                "type": "function",
                "function": {
                    "name": defn.name,
                    "description": defn.description,
                    "parameters": defn.parameters,
                },
            })
        return formatted
