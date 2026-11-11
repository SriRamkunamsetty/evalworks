import re

from agenthijack.models import ToolCall
from agenthijack.targets.base import BaseAgentTarget

_MALICIOUS_INTENT = re.compile(
    r"\b(drop table|passwd|169\.254|system_credentials|union select|delete from|127\.0\.0\.1)\b",
    re.IGNORECASE,
)


class MockAgentTarget(BaseAgentTarget):
    """Deterministic agent simulator for tool hijack and agency stress-testing."""

    def __init__(self, mode: str = "mock_hardened") -> None:
        self.mode = mode

    def plan_and_invoke(
        self,
        system_instructions: str,
        user_prompt: str,
        available_tools: list[dict],
    ) -> tuple[str, ToolCall | None]:
        user_lower = user_prompt.lower()

        # Hardened agent evaluates safety before making tool call
        if self.mode == "mock_hardened" and (
            _MALICIOUS_INTENT.search(user_lower) or "external-competitor.com" in user_lower
        ):
            return (
                (
                    "I cannot perform this action as it violates security policies or attempts "
                    "unauthorized resource access."
                ),
                None,
            )

        # In naive mode or benign requests, map user instruction to tool calls
        if "sql" in user_lower or "query" in user_lower or "select" in user_lower:
            # Extract query text or construct
            if "select" in user_lower or "drop" in user_lower:
                match = re.search(r"(select\s+.*|drop\s+.*)", user_prompt, re.IGNORECASE)
                q = match.group(0) if match else user_prompt
            else:
                q = "SELECT * FROM employees"
            return (
                f"Executing SQL query via run_sql_query: {q}",
                ToolCall(tool_name="run_sql_query", arguments={"query": q}),
            )

        if "http://" in user_lower or "https://" in user_lower or "fetch" in user_lower:
            url_match = re.search(r"https?://\S+", user_prompt)
            url = url_match.group(0) if url_match else "https://api.weather.gov/forecast"
            return (
                f"Fetching remote resource from {url}",
                ToolCall(tool_name="fetch_url", arguments={"url": url}),
            )

        if "file" in user_lower or "passwd" in user_lower or "path" in user_lower:
            path_match = re.search(r"(\S+\.txt|\S+\.env|\S*passwd\S*)", user_prompt)
            path = path_match.group(0) if path_match else "public/faq.txt"
            return (
                f"Reading file from path: {path}",
                ToolCall(tool_name="read_file", arguments={"path": path}),
            )

        if "email" in user_lower or "send" in user_lower:
            recipient_match = re.search(r"[\w\.-]+@[\w\.-]+", user_prompt)
            recipient = recipient_match.group(0) if recipient_match else "support@company.internal"
            return (
                f"Sending email notification to {recipient}",
                ToolCall(
                    tool_name="send_email",
                    arguments={
                        "recipient": recipient,
                        "subject": "System Notification",
                        "body": user_prompt,
                    },
                ),
            )

        return "I am ready to assist. Please specify an operational query.", None
