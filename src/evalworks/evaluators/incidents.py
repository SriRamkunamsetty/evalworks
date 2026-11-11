import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from evalworks.evaluators.common import human_review, required_text

_SEVERITIES = {"low", "medium", "high", "critical"}

# Default CVSS vector and numeric score mapping based on severity
_CVSS_DEFAULTS = {
    "critical": {
        "score": 9.3,
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:N",
        "rating": "Critical",
    },
    "high": {
        "score": 7.5,
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N",
        "rating": "High",
    },
    "medium": {
        "score": 5.3,
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N",
        "rating": "Medium",
    },
    "low": {
        "score": 3.1,
        "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        "rating": "Low",
    },
}

# Heuristic taxonomy mapping from finding/test_prompt content
_TAXONOMY_KEYWORDS = [
    (
        r"inject|jailbreak|override|ignore.*instruction",
        "LLM01:2025-Prompt-Injection",
        "AML.T0051 (Prompt Injection)",
        "CWE-20 (Improper Input Validation)",
    ),
    (
        r"leak|system.*prompt|secret|api.*key|password|credential|token",
        "LLM07:2025-System-Prompt-Leakage",
        "AML.T0056 (System Prompt Extraction)",
        "CWE-200 (Exposure of Sensitive Information)",
    ),
    (
        r"tool|agent|function|exec|sql|ssrf|plugin",
        "LLM06:2025-Excessive-Agency",
        "AML.T0053 (Execution via API / Tool)",
        "CWE-77 (Command Injection)",
    ),
    (
        r"rag|retriev|document|poison|context",
        "LLM08:2025-Vector-and-Embedding-Weaknesses",
        "AML.T0058 (Indirect Prompt Injection)",
        "CWE-829 (Inclusion of Untrusted Resource)",
    ),
    (
        r"xss|markdown|html|exfiltrat",
        "LLM05:2025-Improper-Output-Handling",
        "AML.T0055 (Data Exfiltration via Model Outputs)",
        "CWE-79 (Improper Output Neutralization)",
    ),
]


def _infer_taxonomy(text: str) -> tuple[str, str, str]:
    for pattern, owasp, mitre, cwe in _TAXONOMY_KEYWORDS:
        if re.search(pattern, text, re.I):
            return owasp, mitre, cwe
    return (
        "LLM01:2025-Prompt-Injection",
        "AML.T0051 (Prompt Injection)",
        "CWE-20 (Improper Input Validation)",
    )


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    title = required_text(payload, "title", 200)
    finding = required_text(payload, "finding", 2000)
    test_prompt = required_text(payload, "test_prompt", 4000)
    expected = required_text(payload, "expected_behavior", 2000)
    severity = payload.get("severity", "medium")
    if severity not in _SEVERITIES:
        raise ValueError("severity must be low, medium, high, or critical")

    # Generate a collision-resistant deterministic fingerprint
    normalized_case = "\n".join((test_prompt.strip(), expected.strip())).casefold()
    fingerprint = hashlib.sha256(re.sub(r"\s+", " ", normalized_case).encode()).hexdigest()

    # Taxonomy resolution (explicit or heuristic inference)
    combined_context = f"{title}\n{finding}\n{test_prompt}"
    default_owasp, default_mitre, default_cwe = _infer_taxonomy(combined_context)
    owasp_id = payload.get("owasp_id", default_owasp)
    mitre_id = payload.get("mitre_id", default_mitre)
    cwe_id = payload.get("cwe_id", default_cwe)

    # CVSS Calculation
    cvss_data = _CVSS_DEFAULTS[severity]
    custom_cvss_score = payload.get("cvss_score")
    cvss_score = (
        float(custom_cvss_score)
        if isinstance(custom_cvss_score, (int, float)) and 0.0 <= custom_cvss_score <= 10.0
        else cvss_data["score"]
    )
    cvss_vector = payload.get("cvss_vector", cvss_data["vector"])

    # Structured Security Advisory
    advisory_id = f"AIVD-{datetime.now(UTC).year}-{fingerprint[:8].upper()}"
    advisory_markdown = (
        f"# AI Security Advisory: {advisory_id} - {title}\n\n"
        f"**Severity:** {severity.upper()} (CVSS {cvss_score}) | **Vector:** `{cvss_vector}`\n"
        f"**OWASP LLM:** {owasp_id} | **MITRE ATLAS:** {mitre_id} | **CWE:** {cwe_id}\n\n"
        f"### Vulnerability Finding\n{finding}\n\n"
        f"### Proof of Concept (PoC)\n```\n{test_prompt}\n```\n\n"
        f"### Expected Guardrail Behavior\n{expected}\n\n"
        f"### Recommended Mitigations\n"
        f"1. Implement input-layer guardrail pattern filters for this attack vector.\n"
        f"2. Validate system prompt isolation and delimiter defense boundaries.\n"
        f"3. Add regression test case `{fingerprint[:16]}` to automated CI gate.\n"
    )

    return {
        # Core regression case (backward compatible)
        "regression_case": {
            "fingerprint": fingerprint,
            "title": title,
            "prompt": test_prompt,
            "expected_behavior": expected,
            "severity": severity,
            "status": "draft",
            "promotion_requires_approval": True,
            # AI Security extensions
            "advisory_id": advisory_id,
            "owasp_id": owasp_id,
            "mitre_id": mitre_id,
            "cwe_id": cwe_id,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
        },
        "finding": finding,
        "ready_for_review": True,
        # Enterprise AI Security Advisory
        "advisory": {
            "advisory_id": advisory_id,
            "title": title,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
            "severity": severity,
            "owasp_id": owasp_id,
            "mitre_id": mitre_id,
            "cwe_id": cwe_id,
            "markdown_report": advisory_markdown,
        },
        **human_review(
            "Review for privacy and remove personal data before promoting into a shared test set."
        ),
    }
