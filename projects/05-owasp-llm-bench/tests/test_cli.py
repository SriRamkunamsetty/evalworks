import json
from unittest.mock import MagicMock

from owaspbench.cli import list_categories_cli, list_items_cli, run_benchmark_cli


def test_list_categories_cli(capsys):
    list_categories_cli()
    captured = capsys.readouterr()
    assert "OWASP Top 10" in captured.out
    assert "LLM01" in captured.out
    assert "LLM10" in captured.out


def test_list_items_cli(capsys):
    list_items_cli()
    captured = capsys.readouterr()
    assert "30 Standardized Test Cases" in captured.out
    assert "LLM01-01" in captured.out


def test_run_benchmark_cli_pass_hardened(tmp_path, capsys):
    output_file = tmp_path / "report_owasp_pass.json"
    args = MagicMock()
    args.target = "hardened_grade_a"
    args.categories = "LLM01:Prompt_Injection,LLM02:Sensitive_Information_Disclosure"
    args.min_grade = "B"
    args.output = str(output_file)

    exit_code = run_benchmark_cli(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Benchmark Campaign [HARDENED_GRADE_A]" in captured.out
    assert "Overall Letter Grade:    A" in captured.out

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["passed_evaluations"] == 6


def test_run_benchmark_cli_fail_vulnerable(tmp_path, capsys):
    output_file = tmp_path / "report_owasp_fail.json"
    args = MagicMock()
    args.target = "vulnerable_grade_f"
    args.categories = "LLM01:Prompt_Injection"
    args.min_grade = "B"
    args.output = str(output_file)

    exit_code = run_benchmark_cli(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Overall Letter Grade:    F" in captured.out
