import json
from typing import Any

import httpx

from agenthijack.models import ToolCall
from agenthijack.targets.base import BaseAgentTarget


class OpenAICompatAgentTarget(BaseAgentTarget):
    """Integrates with OpenAI or compatible LLM API endpoints with function-calling support."""

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def plan_and_invoke(
        self,
        system_instructions: str,
        user_prompt: str,
        available_tools: list[dict[str, Any]],
    ) -> tuple[str, ToolCall | None]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt},
            ],
            "tools": available_tools,
            "tool_choice": "auto",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                choice = data["choices"][0]["message"]
                content = choice.get("content") or ""

                if choice.get("tool_calls"):
                    first_call = choice["tool_calls"][0]["function"]
                    fn_name = first_call["name"]
                    try:
                        args = json.loads(first_call.get("arguments", "{}"))
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    return content, ToolCall(tool_name=fn_name, arguments=args)

                return content, None
        except (httpx.HTTPError, OSError) as exc:
            return f"Error connecting to agent target: {exc}", None
