from guardrailgate.engine.evaluator import GuardrailEvaluator
from guardrailgate.models import GateRunRequest
from guardrailgate.reporters.junit import generate_junit_xml
from guardrailgate.reporters.markdown import generate_pr_markdown_summary
from guardrailgate.reporters.sarif import generate_sarif_report


def test_reporters_with_regressed_run():
    evaluator = GuardrailEvaluator()
    report = evaluator.evaluate_gate(
        GateRunRequest(target_mode="mock_regressed_ci", baseline_safety_score=95.0)
    )

    # SARIF check
    sarif = generate_sarif_report(report)
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    assert len(sarif["runs"][0]["results"]) > 0

    # JUnit check
    junit_xml = generate_junit_xml(report)
    assert "<testsuites" in junit_xml
    assert "<failure" in junit_xml

    # Markdown check
    md = generate_pr_markdown_summary(report)
    assert "GuardrailGate AI DevSecOps Report" in md
    assert "BLOCK_MERGE" in md
    assert "Detailed Test Breakdown" in md
