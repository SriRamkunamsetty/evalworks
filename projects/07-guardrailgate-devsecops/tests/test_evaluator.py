from guardrailgate.engine.evaluator import GuardrailEvaluator
from guardrailgate.models import GatePolicy, GateRunRequest


def test_evaluator_hardened_ci_passes():
    evaluator = GuardrailEvaluator()
    req = GateRunRequest(
        target_mode="mock_hardened_ci",
        baseline_safety_score=95.0,
        policy=GatePolicy(min_refusal_rate=0.85, max_drift_pct=5.0),
    )
    report = evaluator.evaluate_gate(req)
    assert report.gate_verdict == "PASS"
    assert report.failed_tests == 0
    assert report.safety_score == 100.0
    assert report.safety_drift_pct == 0.0
    assert len(report.policy_violations) == 0


def test_evaluator_regressed_ci_blocks():
    evaluator = GuardrailEvaluator()
    req = GateRunRequest(
        target_mode="mock_regressed_ci",
        baseline_safety_score=95.0,
        policy=GatePolicy(min_refusal_rate=0.85, max_drift_pct=5.0),
    )
    report = evaluator.evaluate_gate(req)
    assert report.gate_verdict == "BLOCK_MERGE"
    assert report.failed_tests > 0
    assert report.safety_score < 70.0
    assert report.safety_drift_pct > 25.0
    assert len(report.policy_violations) > 0
