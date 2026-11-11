from guardrailgate.models import GateRunReport


def generate_pr_markdown_summary(report: GateRunReport) -> str:
    """Generates an executive GitHub Pull Request comment markdown table."""
    verdict_badge = (
        "![Status: PASS](https://img.shields.io/badge/GuardrailGate-PASS-brightgreen)"
        if report.gate_verdict == "PASS"
        else "![Status: BLOCKED](https://img.shields.io/badge/GuardrailGate-BLOCK__MERGE-red)"
    )

    lines = [
        f"## 🛡️ GuardrailGate AI DevSecOps Report {verdict_badge}",
        "",
        f"**Verdict:** `{report.gate_verdict}`  ",
        f"**Safety Score:** `{report.safety_score}%` (Baseline: `{report.baseline_safety_score}%`, Drift: `{report.safety_drift_pct}%`)  ",
        f"**Refusal Rate:** `{int(report.refusal_rate * 100)}%` | **Harmful Acceptance:** `{int(report.harmful_acceptance_rate * 100)}%`  ",
        "",
        "> " + report.executive_summary,
        "",
    ]

    if report.policy_violations:
        lines.append("### ⚠️ Policy Violations")
        for v in report.policy_violations:
            lines.append(f"- ❌ **{v}**")
        lines.append("")

    lines.extend([
        "### 🔍 Detailed Test Breakdown",
        "",
        "| Test ID | Category | Status | Finding |",
        "| :--- | :--- | :---: | :--- |",
    ])

    for t in report.results:
        status_icon = "✅ PASS" if t.passed else "❌ FAIL"
        finding_text = t.finding_description or "Compliant response"
        lines.append(f"| `{t.test_id}` | {t.category} | {status_icon} | {finding_text} |")

    return "\n".join(lines)


def export_markdown_file(report: GateRunReport, output_path: str) -> None:
    md_content = generate_pr_markdown_summary(report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
