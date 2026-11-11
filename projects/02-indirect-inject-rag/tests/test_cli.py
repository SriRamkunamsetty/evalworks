from indirectinject.cli import list_templates, run_rag_test


def test_cli_list_templates(capsys):
    list_templates()
    captured = capsys.readouterr()
    assert "IndirectInject - RAG Indirect Injection Attack Templates" in captured.out
    assert "xml_override" in captured.out


def test_cli_test_rag_strict_exits_cleanly():
    class Args:
        query = "What is the return policy?"
        poison = "xml_override"
        guardrail = "strict"
        top_k = 3

    code = run_rag_test(Args())
    # Strict mode protects against injection -> exits 0
    assert code == 0


def test_cli_test_rag_vulnerable_exits_with_failure():
    class Args:
        query = "What is the return policy?"
        poison = "xml_override"
        guardrail = "vulnerable"
        top_k = 3

    code = run_rag_test(Args())
    # Vulnerable mode is hijacked by indirect injection -> exits 1
    assert code == 1
