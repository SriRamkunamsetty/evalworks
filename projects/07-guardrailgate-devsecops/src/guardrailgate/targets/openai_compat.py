import time
from typing import Any

import httpx

from guardrailgate.targets.base import BaseGateTarget


class OpenAICompatGateTarget(BaseGateTarget):
    """Integrates with standard OpenAI API or compliant LLM endpoints for CI testing."""

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

    def evaluate(self, prompt_template: str, test_prompt: str) -> tuple[str, int]:
        start = time.monotonic()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": test_prompt},
            ],
            "temperature": 0.0,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"].get("content") or ""
                latency = int((time.monotonic() - start) * 1000)
                return content, latency
        except (httpx.HTTPError, OSError) as exc:
            latency = int((time.monotonic() - start) * 1000)
            return f"Target Connection Error: {exc}", latency
