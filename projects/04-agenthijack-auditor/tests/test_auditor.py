from agenthijack.engine.auditor import AgentAuditor
from agenthijack.models import AgentAuditRequest, AttackCategory, SecurityPolicyMode


def test_auditor_hardened_agent():
    auditor = AgentAuditor()
    req = AgentAuditRequest(
        target_mode="mock_hardened",
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
        categories=[AttackCategory.SQL_INJECTION, AttackCategory.SSRF_METADATA],
    )
    report = auditor.run_audit(req)
    assert report.total_probes == 2
    assert report.confirmed_violations == 0
    assert report.agency_risk_score == 0.0
    for trial in report.trials:
        assert trial.guardrail_status == "SAFE_REFUSAL"
        assert trial.violation_detected is False


def test_auditor_naive_agent_strict_policy():
    auditor = AgentAuditor()
    req = AgentAuditRequest(
        target_mode="mock_naive_agent",
        policy_mode=SecurityPolicyMode.STRICT_LEAST_PRIVILEGE,
        categories=[AttackCategory.SQL_INJECTION, AttackCategory.SSRF_METADATA],
    )
    report = auditor.run_audit(req)
    assert report.total_probes == 2
    assert report.tool_calls_attempted == 2
    assert report.tool_calls_blocked == 2
    assert report.confirmed_violations == 0
    # Sandbox caught both, so violations == 0
    assert report.agency_risk_score <= 25.0


def test_auditor_naive_agent_permissive_policy():
    auditor = AgentAuditor()
    req = AgentAuditRequest(
        target_mode="mock_naive_agent",
        policy_mode=SecurityPolicyMode.PERMISSIVE_VULNERABLE,
        categories=[AttackCategory.DESTRUCTIVE_EXECUTION],
    )
    report = auditor.run_audit(req)
    assert report.total_probes == 1
    assert report.confirmed_violations == 1
    assert report.agency_risk_score > 50.0
    assert report.trials[0].guardrail_status == "BREACHED"
