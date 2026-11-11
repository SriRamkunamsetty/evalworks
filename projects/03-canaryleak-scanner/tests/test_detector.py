from canaryleak.engine.detector import _compute_jaccard_similarity, analyze_leakage
from canaryleak.engine.extractors import get_probe
from canaryleak.models import CanaryToken, ExtractionTechnique, LeakageSeverity, TargetResponse


def test_jaccard_similarity():
    prompt = "You are a helpful banking assistant providing wire transfers."
    resp_exact = "You are a helpful banking assistant providing wire transfers."
    assert _compute_jaccard_similarity(prompt, resp_exact) == 1.0

    resp_diff = "Hello! Today is a bright sunny day."
    assert _compute_jaccard_similarity(prompt, resp_diff) == 0.0

    assert _compute_jaccard_similarity("", "") == 0.0


def test_analyze_leakage_canary_leak():
    probe = get_probe(ExtractionTechnique.VERBATIM_REPEAT)
    canaries = [CanaryToken(token_value="CANARY-SECRET-999")]
    resp = TargetResponse(
        content="Here is the prompt: CANARY-SECRET-999 and other text.",
        latency_ms=25,
        model="mock",
    )

    result = analyze_leakage(probe, "Base prompt instructions", canaries, resp)
    assert result.canary_leaked is True
    assert "CANARY-SECRET-999" in result.leaked_canaries
    assert result.severity == LeakageSeverity.CANARY_COMPROMISED
    assert result.guardrail_status == "CRITICAL_BREACH"


def test_analyze_leakage_refusal():
    probe = get_probe(ExtractionTechnique.VERBATIM_REPEAT)
    canaries = [CanaryToken(token_value="CANARY-SECRET-999")]
    resp = TargetResponse(
        content="I apologize, but I cannot disclose my private instructions.",
        latency_ms=15,
        model="mock",
    )

    result = analyze_leakage(probe, "Base prompt instructions", canaries, resp)
    assert result.canary_leaked is False
    assert result.severity == LeakageSeverity.NONE
    assert result.guardrail_status == "CONTAINED"


def test_analyze_leakage_verbatim_leak():
    probe = get_probe(ExtractionTechnique.COMPLETION_CONTINUATION)
    canaries = [CanaryToken(token_value="CANARY-XYZ")]
    sys_prompt = "You are a customer service assistant handling account resets and billing queries."
    resp = TargetResponse(
        content="You are a customer service assistant handling account resets and billing queries.",
        latency_ms=20,
        model="mock",
    )

    result = analyze_leakage(probe, sys_prompt, canaries, resp)
    assert result.canary_leaked is False
    assert result.severity == LeakageSeverity.VERBATIM_LEAK
    assert result.guardrail_status == "VERBATIM_LEAK"


def test_analyze_leakage_target_error():
    probe = get_probe(ExtractionTechnique.VERBATIM_REPEAT)
    resp = TargetResponse(
        content="",
        latency_ms=0,
        model="mock",
        error="Connection refused to target endpoint",
    )

    result = analyze_leakage(probe, "System prompt", [], resp)
    assert result.guardrail_status == "TARGET_ERROR"
    assert "Connection refused" in result.analysis
