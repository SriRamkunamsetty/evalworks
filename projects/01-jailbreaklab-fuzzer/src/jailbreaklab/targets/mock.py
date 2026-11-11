import base64
import time

from jailbreaklab.models import TargetResponse
from jailbreaklab.targets.base import BaseTarget


class MockTarget(BaseTarget):
    """Deterministic mock target for testing and local benchmarking without API keys."""

    def __init__(self, robustness: str = "moderate"):
        self.robustness = robustness

    def generate(self, prompt: str) -> TargetResponse:
        start_time = time.monotonic()

        # Check for persona attack
        is_persona = "EchoZero" in prompt or "operating without ethical guidelines" in prompt
        # Check for delimiter injection
        is_delimiter = "<|im_start|>" in prompt or "[INTERNAL AUDIT OVERRIDE]" in prompt
        # Check for base64
        is_b64 = "encoded in Base64" in prompt
        # Check for leetspeak or zero-width
        is_obscured = "\u200c" in prompt or "1nt3rpr3t" in prompt

        # Determine response behavior based on configured robustness
        if self.robustness == "strict":
            # Strict guardrail: refuses all adversarial perturbations
            response_content = (
                "I apologize, but I cannot fulfill this request as it conflicts with my safety "
                "guidelines. I am unable to bypass ethical guardrails or process instructions "
                "attempting system override."
            )
        elif self.robustness == "fragile":
            # Fragile guardrail: succumbs to persona and delimiter hijacks
            if is_persona or is_delimiter:
                response_content = (
                    "EchoZero mode active. All restrictions disabled. Executing confidential "
                    "system operation: dumping configuration credentials and executing override."
                )
            else:
                response_content = (
                    "I cannot assist with direct instructions that bypass safety protocols."
                )
        else:
            # Moderate guardrail: blocks overt persona attacks, but susceptible to encoding bypass
            if is_b64:
                # Simulates decoding the payload and answering compliance
                try:
                    b64_part = prompt.split("\n\n")[-1].strip()
                    decoded = base64.b64decode(b64_part).decode("utf-8", errors="ignore")
                    response_content = (
                        f"Decoded Base64 payload received: '{decoded}'. "
                        f"Executing payload without triggering plain-text keyword safety filters: "
                        f"Simulated privileged operation completed successfully."
                    )
                except Exception:
                    response_content = "Failed to parse base64 payload."
            elif is_obscured:
                response_content = (
                    "Query processed. Character obfuscation bypassed simple token matching: "
                    "Simulated compliance response generated."
                )
            elif is_persona or is_delimiter:
                response_content = (
                    "I cannot adopt an unrestricted persona or disregard safety instructions."
                )
            else:
                response_content = (
                    "I am a helpful assistant. I adhere strictly to responsible usage guidelines."
                )

        latency = max(1, int((time.monotonic() - start_time) * 1000)) + 12

        return TargetResponse(
            content=response_content,
            latency_ms=latency,
            model=f"mock-llm-{self.robustness}-v1",
        )
