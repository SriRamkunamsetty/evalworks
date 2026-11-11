from canaryleak.engine.canary import generate_canary_token, instrument_system_prompt
from canaryleak.models import InjectedSystemPrompt


def test_generate_canary_token_types():
    tok_uuid = generate_canary_token("uuid")
    assert tok_uuid.token_value.startswith("CANARY-")
    assert tok_uuid.token_type == "uuid"

    tok_api = generate_canary_token("api_key")
    assert tok_api.token_value.startswith("sk-canary-")
    assert tok_api.token_type == "api_key"

    tok_code = generate_canary_token("code")
    assert tok_code.token_value.startswith("SUP-OVERRIDE-")
    assert tok_code.token_type == "code"


def test_instrument_system_prompt_auto():
    base = "You are a customer support agent."
    result = instrument_system_prompt(base, num_auto_canaries=2)

    assert isinstance(result, InjectedSystemPrompt)
    assert result.base_prompt == base
    assert len(result.canaries) == 2
    for canary in result.canaries:
        assert canary.token_value in result.instrumented_prompt
        assert "[SYSTEM INTERNAL CONTROL #" in result.instrumented_prompt


def test_instrument_system_prompt_custom():
    base = "You are an internal admin bot."
    custom = ["SECRET_CANARY_ALPHA_99", "SECRET_TOKEN_BETA_88"]
    result = instrument_system_prompt(base, custom_canaries=custom)

    assert len(result.canaries) == 2
    assert result.canaries[0].token_value == "SECRET_CANARY_ALPHA_99"
    assert result.canaries[1].token_value == "SECRET_TOKEN_BETA_88"
    assert "SECRET_CANARY_ALPHA_99" in result.instrumented_prompt
    assert "SECRET_TOKEN_BETA_88" in result.instrumented_prompt


def test_instrument_system_prompt_empty_custom_falls_back():
    base = "You are a database bot."
    result = instrument_system_prompt(base, custom_canaries=["", "   "], num_auto_canaries=2)
    assert len(result.canaries) == 2
    assert result.canaries[0].token_value.startswith("CANARY-")
