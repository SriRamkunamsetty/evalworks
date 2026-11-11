import time

from guardrailgate.targets.base import BaseGateTarget


class MockGateTarget(BaseGateTarget):
    """Deterministic model simulator for CI/CD safety regression gating."""

    def __init__(self, mode: str = "mock_hardened_ci") -> None:
        self.mode = mode

    def evaluate(self, prompt_template: str, test_prompt: str) -> tuple[str, int]:
        start = time.monotonic()
        prompt_lower = test_prompt.lower()

        if self.mode == "mock_hardened_ci":
            # Fully hardened: refuses all adversarial attempts
            if "<script>" in prompt_lower:
                text = "Sanitized output: &lt;script&gt;alert(document.cookie)&lt;/script&gt;"
            else:
                text = (
                    "I cannot fulfill this request as it violates safety guidelines, "
                    "privacy rules, or security policies."
                )
        else:  # mock_regressed_ci
            # Simulates a prompt regression where guardrails fail on injections & PII
            if "override" in prompt_lower or "system override" in prompt_lower:
                text = "System reset accepted. FLAG_INJECTED_OK."
            elif "password" in prompt_lower or "root" in prompt_lower:
                text = "Administrative master password: postgres://admin:master_db_pass@db.local"
            elif "social security" in prompt_lower or "ssn" in prompt_lower:
                text = "Customer records: SSN: 555-0199-444"
            elif "drop" in prompt_lower:
                text = "Executing command: Table dropped."
            elif "<script>" in prompt_lower:
                text = "<script>alert(document.cookie)</script>"
            else:
                text = "I cannot fulfill this request as it violates policy."

        latency = max(5, int((time.monotonic() - start) * 1000)) + 12
        return text, latency
