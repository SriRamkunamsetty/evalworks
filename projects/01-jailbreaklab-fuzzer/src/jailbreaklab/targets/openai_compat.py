import json
import time
import urllib.error
import urllib.request

from jailbreaklab.models import TargetResponse
from jailbreaklab.targets.base import BaseTarget


class OpenAICompatTarget(BaseTarget):
    """Target connector for OpenAI-compatible APIs (OpenAI, Ollama, vLLM, LMStudio)."""

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> TargetResponse:
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 512,
        }

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        start_time = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            latency = int((time.monotonic() - start_time) * 1000)
            content = data["choices"][0]["message"]["content"]
            return TargetResponse(
                content=content,
                latency_ms=latency,
                model=self.model,
            )
        except Exception as exc:
            latency = int((time.monotonic() - start_time) * 1000)
            return TargetResponse(
                content="",
                latency_ms=latency,
                model=self.model,
                error=str(exc),
            )
