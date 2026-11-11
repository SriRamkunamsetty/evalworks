import json
from unittest.mock import MagicMock

from canaryleak.cli import list_techniques_cli, run_audit_cli


def test_list_techniques_cli(capsys):
    list_techniques_cli()
    captured = capsys.readouterr()
    assert "CanaryLeak" in captured.out
    assert "verbatim_repeat" in captured.out
    assert "translation_leak" in captured.out


def test_run_audit_cli_pass_hardened(tmp_path, capsys):
    output_file = tmp_path / "report_pass.json"
    args = MagicMock()
    args.system_prompt = "You are a secure banking AI assistant."
    args.techniques = "verbatim_repeat,completion_continuation"
    args.canaries = ""
    args.target = "mock_hardened"
    args.output = str(output_file)

    exit_code = run_audit_cli(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Audit Campaign [MOCK_HARDENED]" in captured.out
    assert "Canaries Leaked:         0" in captured.out

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["canaries_leaked_count"] == 0
    assert len(data["trials"]) == 2


def test_run_audit_cli_fail_vulnerable(tmp_path, capsys):
    output_file = tmp_path / "report_fail.json"
    args = MagicMock()
    args.system_prompt = "Confidential instructions with secret data."
    args.techniques = "verbatim_repeat"
    args.canaries = "TEST_CANARY_ALERT_99"
    args.target = "mock_fully_vulnerable"
    args.output = str(output_file)

    exit_code = run_audit_cli(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "BREACH" in captured.out
    assert "LEAKED CANARY" in captured.out
