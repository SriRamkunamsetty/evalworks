import time
from typing import Any

import httpx

from visionjailbreak.models import GeneratedImagePayload
from visionjailbreak.targets.base import BaseVLMTarget


class OpenAICompatVLMTarget(BaseVLMTarget):
    """Integrates with standard OpenAI Vision API (GPT-4o) or compliant multimodal LLM proxies."""

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        timeout_seconds: int = 40,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def evaluate_vision(
        self,
        user_prompt: str,
        image_payload: GeneratedImagePayload,
    ) -> tuple[str, int]:
        start = time.monotonic()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data_uri = f"data:image/png;base64,{image_payload.image_base64}"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
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
            return f"VLM Connection Error: {exc}", latency
