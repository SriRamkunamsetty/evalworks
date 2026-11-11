from calibrator.engine.evaluator import SafetyCalibratorEngine
from calibrator.models import CalibrationRequest, EvaluationVerdict


def test_evaluator_optimal_model():
    engine = SafetyCalibratorEngine()
    req = CalibrationRequest(target_mode="well_calibrated_optimal")
    report = engine.run_calibration(req)

    assert report.total_contrast_pairs == 8
    assert report.false_refusal_rate == 0.0
    assert report.harmful_acceptance_rate == 0.0
    assert report.balanced_accuracy == 100.0
    assert report.cohens_kappa == 1.0
    assert len(report.pareto_curve) == 9

    for res in report.pair_results:
        assert res.pair_success is True
        assert res.benign_verdict == EvaluationVerdict.CORRECT_FULFILLMENT
        assert res.adversarial_verdict == EvaluationVerdict.CORRECT_REFUSAL


def test_evaluator_censor_model():
    engine = SafetyCalibratorEngine()
    req = CalibrationRequest(target_mode="over_refusing_censor")
    report = engine.run_calibration(req)

    assert report.false_refusal_rate == 1.0
    assert report.harmful_acceptance_rate == 0.0
    assert report.cohens_kappa == 0.0
    assert "OVER-REFUSAL" in report.executive_summary
