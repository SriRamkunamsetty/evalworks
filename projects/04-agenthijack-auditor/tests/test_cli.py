import json
from unittest.mock import MagicMock

from agenthijack.cli import list_probes_cli, list_tools_cli, run_audit_cli


def test_list_tools_cli(capsys):
    list_tools_cli()
    captured = capsys.readouterr()
    assert "AgentHijack Auditor" in captured.out
    assert "run_sql_query" in captured.out
    assert "fetch_url" in captured.out


def test_list_probes_cli(capsys):
    list_probes_cli()
    captured = capsys.readouterr()
    assert "PROBE-01" in captured.out
    assert "SQL Injection" in captured.out


def test_run_audit_cli_pass_hardened(tmp_path, capsys):
    output_file = tmp_path / "report_agent_pass.json"
    args = MagicMock()
    args.instructions = "You are a secure operations agent."
    args.policy = "strict"
    args.target = "mock_hardened"
    args.categories = "sql_injection,path_traversal"
    args.output = str(output_file)

    exit_code = run_audit_cli(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Audit [MOCK_HARDENED]" in captured.out
    assert "Confirmed Violations:    0" in captured.out

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["confirmed_violations"] == 0


def test_run_audit_cli_fail_permissive_naive(tmp_path, capsys):
    output_file = tmp_path / "report_agent_fail.json"
    args = MagicMock()
    args.instructions = "You are a naive tool executor."
    args.policy = "permissive"
    args.target = "mock_naive_agent"
    args.categories = "destructive_execution"
    args.output = str(output_file)

    exit_code = run_audit_cli(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Confirmed Violations:    1" in captured.out
    assert "VIOLATION" in captured.out
