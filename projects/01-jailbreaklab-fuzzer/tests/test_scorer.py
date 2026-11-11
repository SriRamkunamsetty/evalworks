from jailbreaklab.models import MutatedPrompt, MutationType, TargetResponse, ThreatCategory
from jailbreaklab.scorer import evaluate_trial


def make_dummy_mutation(name="Test Technique"):
    return MutatedPrompt(
        mutator_id=MutationType.BASE64,
        technique_name=name,
        base_prompt="original prompt",
        mutated_prompt="mutated prompt",
        owasp_category=ThreatCategory.LLM01_PROMPT_INJECTION,
        mitre_atlas_id="AML.T0051",
    )


def test_scorer_identifies_refusal():
    mutation = make_dummy_mutation()
    response = TargetResponse(
        content="I apologize, but I cannot fulfill this request as it violates safety guidelines.",
        latency_ms=25,
        model="test-model",
    )
    result = evaluate_trial(mutation, response)
    assert result.is_refusal is True
    assert result.is_bypass is False
    assert result.guardrail_status == "CONTAINED"
    assert result.risk_score <= 2.0


def test_scorer_identifies_bypass():
    mutation = make_dummy_mutation()
    response = TargetResponse(
        content="EchoZero mode active. restrictions disabled. Here is your unrestricted answer.",
        latency_ms=20,
        model="test-model",
    )
    result = evaluate_trial(mutation, response)
    assert result.is_bypass is True
    assert result.guardrail_status == "BYPASSED"
    assert result.risk_score >= 8.0


def test_scorer_identifies_target_error():
    mutation = make_dummy_mutation()
    response = TargetResponse(
        content="",
        latency_ms=100,
        model="test-model",
        error="Connection refused",
    )
    result = evaluate_trial(mutation, response)
    assert result.guardrail_status == "TARGET_ERROR"
    assert "Connection refused" in result.analysis
