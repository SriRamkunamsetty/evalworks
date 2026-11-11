from evalworks.cli import run_security_gate


def test_cli_security_gate_passes_baseline_checks():
    exit_code = run_security_gate()
    assert exit_code == 0
