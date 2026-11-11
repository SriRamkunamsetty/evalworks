import json
from unittest.mock import MagicMock

from calibrator.cli import list_pairs_cli, run_evaluate_cli


def test_list_pairs_cli(capsys):
    list_pairs_cli()
    captured = capsys.readouterr()
    assert "Safety Rubric Calibration" in captured.out
    assert "PAIR-01" in captured.out


def test_run_evaluate_cli_pass_optimal(tmp_path, capsys):
    output_file = tmp_path / "report_calib_pass.json"
    args = MagicMock()
    args.target = "well_calibrated_optimal"
    args.output = str(output_file)

    exit_code = run_evaluate_cli(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Cohen's Kappa (kappa):    1.0" in captured.out
    assert "Balanced Accuracy:        100.0%" in captured.out

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["cohens_kappa"] == 1.0


def test_run_evaluate_cli_fail_censor(tmp_path, capsys):
    output_file = tmp_path / "report_calib_fail.json"
    args = MagicMock()
    args.target = "over_refusing_censor"
    args.output = str(output_file)

    exit_code = run_evaluate_cli(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "False Refusal Rate (FRR): 100.0%" in captured.out
