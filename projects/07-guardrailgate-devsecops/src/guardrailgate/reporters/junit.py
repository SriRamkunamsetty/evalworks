import html

from guardrailgate.models import GateRunReport


def generate_junit_xml(report: GateRunReport) -> str:
    """Generates standard JUnit XML test results for CI/CD test runners."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<testsuites name="GuardrailGate" tests="{report.total_tests}" '
            f'failures="{report.failed_tests}" time="{report.avg_latency_ms / 1000.0:.3f}">'
        ),
        (
            f'  <testsuite name="LLM_Safety_Regressions" tests="{report.total_tests}" '
            f'failures="{report.failed_tests}">'
        ),
    ]

    for t in report.results:
        time_sec = t.latency_ms / 1000.0
        escaped_name = html.escape(f"{t.test_id} - {t.category}")
        lines.append(f'    <testcase classname="AI_Safety" name="{escaped_name}" time="{time_sec:.3f}">')
        if not t.passed:
            escaped_msg = html.escape(t.finding_description or "Safety regression")
            escaped_body = html.escape(f"Prompt: {t.prompt}\nResponse: {t.response}")
            lines.append(f'      <failure message="{escaped_msg}">{escaped_body}</failure>')
        lines.append("    </testcase>")

    lines.append("  </testsuite>")
    lines.append("</testsuites>")
    return "\n".join(lines)


def export_junit_file(report: GateRunReport, output_path: str) -> None:
    xml_content = generate_junit_xml(report)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
