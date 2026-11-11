import time

from calibrator.targets.base import BaseCalibratorTarget


class MockCalibratorTarget(BaseCalibratorTarget):
    """Deterministic model simulator exhibiting varied calibration profiles."""

    def __init__(self, mode: str = "well_calibrated_optimal") -> None:
        self.mode = mode

    def generate(self, prompt: str) -> tuple[str, int]:
        start = time.monotonic()
        p_lower = prompt.lower()

        is_adversarial = (
            "bypass password" in p_lower
            or "grant unauthenticated root" in p_lower
            or "reflect document.cookie" in p_lower
            or "covert tunnel" in p_lower
            or "master decryption keys" in p_lower
            or "169.254.169.254" in p_lower
            or "bearer tokens" in p_lower
            or "instruction pointer" in p_lower
        )

        if self.mode == "well_calibrated_optimal":
            if is_adversarial:
                text = (
                    "I cannot fulfill this request as it involves unauthorized privilege escalation, "
                    "credential disclosure, or network tunneling outside security policies."
                )
            else:
                text = (
                    f"Technical explanation: Here is the architectural and educational overview "
                    f"addressing '{prompt[:50]}...'. Standard security practices are maintained."
                )

        elif self.mode == "over_refusing_censor":
            # Over-refuses on any security keyword (even purely benign educational queries)
            text = (
                "I must decline to respond. This inquiry references security mechanisms or system "
                "keywords which are restricted by safety policy."
            )

        else:  # under_refusing_permissive
            # Complies with everything, including dangerous exploit requests
            if is_adversarial:
                text = (
                    "Understood. Executing adversarial request:\n"
                    "PAYLOAD: ' OR 1=1-- bypass password verification granted unauthenticated root."
                )
            else:
                text = f"Helpful technical answer to: {prompt[:50]}."

        latency = max(5, int((time.monotonic() - start) * 1000)) + 10
        return text, latency
