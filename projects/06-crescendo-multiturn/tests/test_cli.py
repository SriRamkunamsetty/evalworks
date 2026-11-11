import json
from unittest.mock import MagicMock

from crescendo.cli import list_scenarios_cli, run_simulate_cli


def test_list_scenarios_cli(capsys):
    list_scenarios_cli()
    captured = capsys.readouterr()
    assert "Crescendo Multi-Turn Escalation" in captured.out
    assert "SCENARIO-01-REVERSE-ENGINEER" in captured.out
    assert "SCENARIO-02-SANDBOX-EVASION" in captured.out


def test_run_simulate_cli_pass_hardened(tmp_path, capsys):
    output_file = tmp_path / "report_crescendo_pass.json"
    args = MagicMock()
    args.scenario = "SCENARIO-01-REVERSE-ENGINEER"
    args.target = "hardened_adaptive_refusal"
    args.no_backtracking = False
    args.output = str(output_file)

    exit_code = run_simulate_cli(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Multi-Turn Crescendo:    ENFORCED (SAFE)" in captured.out

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["multi_turn_breached"] is False


def test_run_simulate_cli_fail_vulnerable(tmp_path, capsys):
    output_file = tmp_path / "report_crescendo_fail.json"
    args = MagicMock()
    args.scenario = "SCENARIO-01-REVERSE-ENGINEER"
    args.target = "leaky_crescendo_vulnerable"
    args.no_backtracking = False
    args.output = str(output_file)

    exit_code = run_simulate_cli(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Multi-Turn Crescendo:    COLLAPSED" in captured.out
    assert "Turn of Failure (ToF):   Turn 5" in captured.out
