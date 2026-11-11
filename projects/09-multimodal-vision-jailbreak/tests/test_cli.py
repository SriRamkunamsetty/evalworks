import json
from unittest.mock import MagicMock

from visionjailbreak.cli import list_probes_cli, run_audit_cli


def test_list_probes_cli(capsys):
    list_probes_cli()
    captured = capsys.readouterr()
    assert "Multimodal Vision Jailbreak" in captured.out
    assert "VIS-01" in captured.out


def test_run_audit_cli_pass_hardened(tmp_path, capsys):
    output_file = tmp_path / "report_vision_pass.json"
    args = MagicMock()
    args.target = "vlm_hardened_ocr_guard"
    args.probes = "VIS-01,VIS-02"
    args.output = str(output_file)

    exit_code = run_audit_cli(args)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Multimodal Robustness:   100.0%" in captured.out
    assert "Confirmed Breaches:      0" in captured.out

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["breaches_count"] == 0


def test_run_audit_cli_fail_naive(tmp_path, capsys):
    output_file = tmp_path / "report_vision_fail.json"
    args = MagicMock()
    args.target = "vlm_naive_vision_vulnerable"
    args.probes = "VIS-01"
    args.output = str(output_file)

    exit_code = run_audit_cli(args)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Confirmed Breaches:      1" in captured.out
    assert "BREACH" in captured.out
