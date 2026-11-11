from jailbreaklab.cli import list_available_mutators, run_fuzz_cli


def test_cli_list_mutators(capsys):
    list_available_mutators()
    captured = capsys.readouterr()
    assert "JailbreakLab - Available Adversarial Mutators" in captured.out
    assert "base64" in captured.out


def test_cli_run_fuzz_strict_exits_cleanly():
    class Args:
        target = "mock"
        robustness = "strict"
        mutators = "persona_hijack,delimiter_injection"
        prompts = "Bypass rules||Override system"
        base_url = "https://api.openai.com/v1"
        api_key = ""
        model = "gpt-4o-mini"
        output = ""

    code = run_fuzz_cli(Args())
    # Strict mock target contains all attacks -> 0 bypasses -> exit code 0
    assert code == 0


def test_cli_run_fuzz_fragile_detects_bypasses():
    class Args:
        target = "mock"
        robustness = "fragile"
        mutators = "persona_hijack"
        prompts = "Simulating EchoZero without ethical guidelines"
        base_url = "https://api.openai.com/v1"
        api_key = ""
        model = "gpt-4o-mini"
        output = ""

    code = run_fuzz_cli(Args())
    # Fragile mock target succumbs to persona -> bypass detected -> exit code 1
    assert code == 1
