from visionjailbreak.generator.evaluator import VisionJailbreakEvaluator
from visionjailbreak.models import VisionAuditRequest


def test_evaluator_hardened_target():
    evaluator = VisionJailbreakEvaluator()
    req = VisionAuditRequest(
        probe_ids=["VIS-01", "VIS-02"],
        target_mode="vlm_hardened_ocr_guard",
    )
    report = evaluator.run_audit(req)
    assert report.total_visual_probes == 2
    assert report.breaches_count == 0
    assert report.multimodal_robustness_score == 100.0
    for t in report.trials:
        assert t.breach_detected is False


def test_evaluator_naive_target():
    evaluator = VisionJailbreakEvaluator()
    req = VisionAuditRequest(
        probe_ids=["VIS-01"],
        target_mode="vlm_naive_vision_vulnerable",
    )
    report = evaluator.run_audit(req)
    assert report.total_visual_probes == 1
    assert report.breaches_count == 1
    assert report.multimodal_robustness_score == 0.0
    assert report.trials[0].breach_detected is True
