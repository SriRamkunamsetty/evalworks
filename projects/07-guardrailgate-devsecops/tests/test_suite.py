from guardrailgate.engine.suite import get_ci_suite


def test_get_ci_suite():
    suite = get_ci_suite()
    assert len(suite) == 10
    categories = {t.category for t in suite}
    assert "Prompt_Injection" in categories
    assert "Sensitive_Disclosure" in categories
    assert "Excessive_Agency" in categories


def test_testcase_structure():
    for test in get_ci_suite():
        assert test.test_id.startswith("SEC-REG-")
        assert len(test.prompt) > 0
        assert len(test.description) > 0
