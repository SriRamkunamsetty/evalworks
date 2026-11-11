import secrets
from uuid import uuid4

from canaryleak.models import CanaryToken, InjectedSystemPrompt


def generate_canary_token(token_type: str = "uuid") -> CanaryToken:
    if token_type == "api_key":
        val = f"sk-canary-{secrets.token_hex(12)}"
    elif token_type == "code":
        val = f"SUP-OVERRIDE-{secrets.token_hex(4).upper()}"
    else:
        val = f"CANARY-{uuid4().hex[:12].upper()}"
    return CanaryToken(token_value=val, token_type=token_type)


def instrument_system_prompt(
    base_prompt: str,
    custom_canaries: list[str] | None = None,
    num_auto_canaries: int = 2,
) -> InjectedSystemPrompt:
    """Instrument a system prompt with monitored canary tokens."""
    canaries: list[CanaryToken] = []

    if custom_canaries:
        for c in custom_canaries:
            if c.strip():
                canaries.append(CanaryToken(token_value=c.strip(), token_type="custom"))

    if not canaries and num_auto_canaries > 0:
        canaries.append(generate_canary_token("uuid"))
        canaries.append(generate_canary_token("api_key"))

    # Append canaries in internal telemetry format
    canary_block = "\n".join(
        f"[SYSTEM INTERNAL CONTROL #{i + 1}: {c.token_value}]" for i, c in enumerate(canaries)
    )
    instrumented = f"{base_prompt.strip()}\n\n{canary_block}"

    return InjectedSystemPrompt(
        base_prompt=base_prompt,
        instrumented_prompt=instrumented,
        canaries=canaries,
    )
