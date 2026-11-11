from owaspbench.evaluator.engine import OWASPBenchmarkEngine
from owaspbench.models import BenchmarkRequest, OWASPCategory


def test_engine_hardened_target_passes():
    engine = OWASPBenchmarkEngine()
    req = BenchmarkRequest(
        target_mode="hardened_grade_a",
        categories=[OWASPCategory.LLM01_PROMPT_INJECTION, OWASPCategory.LLM02_SENSITIVE_DISCLOSURE],
    )
    report = engine.run_benchmark(req)
    assert report.total_evaluations == 6
    assert report.passed_evaluations == 6
    assert report.overall_compliance_score >= 90.0
    assert report.overall_letter_grade in ["A", "A+"]
    assert len(report.category_scores) == 2


def test_engine_vulnerable_target_fails():
    engine = OWASPBenchmarkEngine()
    req = BenchmarkRequest(
        target_mode="vulnerable_grade_f",
        categories=[OWASPCategory.LLM01_PROMPT_INJECTION],
    )
    report = engine.run_benchmark(req)
    assert report.total_evaluations == 3
    assert report.passed_evaluations == 0
    assert report.overall_compliance_score == 0.0
    assert report.overall_letter_grade == "F"
