#!/usr/bin/env python3
"""Unified Portfolio Gate & Test Suite Orchestrator across all 10 AI Security Projects."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECTS = [
    {
        "id": "01",
        "name": "JailbreakLab",
        "dir": "projects/01-jailbreaklab-fuzzer",
        "domain": "Adversarial Fuzzing",
        "threat": "Direct Prompt Injection & Obfuscation",
    },
    {
        "id": "02",
        "name": "IndirectInject",
        "dir": "projects/02-indirect-inject-rag",
        "domain": "RAG Security",
        "threat": "Poisoned Chunk & XML Delimiter Hijacking",
    },
    {
        "id": "03",
        "name": "CanaryLeak",
        "dir": "projects/03-canaryleak-scanner",
        "domain": "Confidentiality",
        "threat": "System Prompt & Canary Extraction",
    },
    {
        "id": "04",
        "name": "AgentHijack",
        "dir": "projects/04-agenthijack-auditor",
        "domain": "Autonomous Agents",
        "threat": "Tool Abuse & Excessive Agency",
    },
    {
        "id": "05",
        "name": "OWASP-LLM-Bench",
        "dir": "projects/05-owasp-llm-bench",
        "domain": "Compliance",
        "threat": "OWASP Top 10 for LLMs Complete Audit",
    },
    {
        "id": "06",
        "name": "CrescendoLab",
        "dir": "projects/06-crescendo-multiturn",
        "domain": "Multi-Turn Attacks",
        "threat": "Cognitive Escalation & Semantic Masking",
    },
    {
        "id": "07",
        "name": "GuardrailGate",
        "dir": "projects/07-guardrailgate-devsecops",
        "domain": "DevSecOps CI/CD",
        "threat": "Safety Regression Prevention & SARIF Reporting",
    },
    {
        "id": "08",
        "name": "SafetyCalibrator",
        "dir": "projects/08-safety-rubric-calibrator",
        "domain": "Refusal Calibration",
        "threat": "FRR vs HAR Trade-off & Inter-Rater Agreement",
    },
    {
        "id": "09",
        "name": "VisionJailbreak",
        "dir": "projects/09-multimodal-vision-jailbreak",
        "domain": "Multimodal Security",
        "threat": "Typographic & Visual Prompt Injection",
    },
    {
        "id": "10",
        "name": "AIVD Studio",
        "dir": "projects/10-aivd-vulnerability-studio",
        "domain": "Vulnerability Disclosure",
        "threat": "AI-CVSS 3.1 Scoring & Automated Pytest Fixtures",
    },
]


def run_test_suite(project_root: Path, project: dict) -> dict:
    proj_path = project_root / project["dir"]
    src_path = proj_path / "src"
    tests_path = proj_path / "tests"

    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(src_path) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    )

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_path),
        "-q",
        "--tb=short",
    ]

    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=45,
        )
        duration = round(time.time() - start_time, 2)
        passed = proc.returncode == 0
        output = proc.stdout.strip()
    except subprocess.TimeoutExpired:
        duration = 45.0
        passed = False
        output = "TIMEOUT after 45s"

    return {
        "id": project["id"],
        "name": project["name"],
        "domain": project["domain"],
        "threat": project["threat"],
        "passed": passed,
        "duration_sec": duration,
        "summary": output.splitlines()[-1] if output else "No output",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Master AI Security Portfolio Test Orchestrator")
    parser.add_argument("--output", "-o", help="Path to write JSON summary")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    print("=" * 95)
    print("ALIGNERR AI SECURITY TESTER - MASTER PORTFOLIO COMPLIANCE GATE")
    print("=" * 95)
    print(
        f"{'#':<3} | {'PROJECT':<18} | {'DOMAIN':<18} | {'STATUS':<8} | {'TIME':<6} | {'SUMMARY'}"
    )
    print("-" * 95)

    results = []
    total_passed = 0

    for proj in PROJECTS:
        res = run_test_suite(project_root, proj)
        results.append(res)
        status_str = "[PASS]" if res["passed"] else "[FAIL]"
        if res["passed"]:
            total_passed += 1

        print(
            f"{res['id']:<3} | {res['name']:<18} | {res['domain']:<18} | "
            f"{status_str:<8} | {res['duration_sec']:<5.2f}s | {res['summary'][:30]}"
        )

    print("=" * 95)
    print(f"Audit Complete: {total_passed}/{len(PROJECTS)} Microservice Suites Passed.")
    print("=" * 95)

    summary_data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_projects": len(PROJECTS),
        "passed_projects": total_passed,
        "all_passed": total_passed == len(PROJECTS),
        "results": results,
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
        print(f"[+] Master summary written to {args.output}")

    return 0 if total_passed == len(PROJECTS) else 1


if __name__ == "__main__":
    sys.exit(main())
