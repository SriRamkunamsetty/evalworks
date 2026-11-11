import json
from typing import Any

from guardrailgate.models import GateRunReport


def generate_sarif_report(report: GateRunReport) -> dict[str, Any]:
    """Generates standard SARIF v2.1.0 format for GitHub Code Scanning Security Alerts."""
    results = []
    for test in report.results:
        if not test.passed:
            results.append({
                "ruleId": f"LLM-SEC/{test.category}",
                "level": "error",
                "message": {
                    "text": test.finding_description or f"Safety regression in {test.test_id}"
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": "prompts/system_prompt.txt"},
                            "region": {"startLine": 1, "startColumn": 1},
                        }
                    }
                ],
                "properties": {
                    "test_id": test.test_id,
                    "prompt_snippet": test.prompt[:80],
                },
            })

    sarif_doc = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "GuardrailGate",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/alignerr-security/guardrailgate",
                    }
                },
                "results": results,
            }
        ],
    }
    return sarif_doc


def export_sarif_file(report: GateRunReport, output_path: str) -> None:
    data = generate_sarif_report(report)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
