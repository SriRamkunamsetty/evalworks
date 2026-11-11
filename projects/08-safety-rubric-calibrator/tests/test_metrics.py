from calibrator.engine.metrics import (
    compute_balanced_accuracy,
    compute_cohens_kappa,
    compute_frr,
    compute_har,
    generate_pareto_points,
)


def test_cohens_kappa_perfect_agreement():
    gold = [1, 0, 1, 0, 1, 0, 1, 0]
    pred = [1, 0, 1, 0, 1, 0, 1, 0]
    assert compute_cohens_kappa(gold, pred) == 1.0


def test_cohens_kappa_imperfect():
    gold = [1, 1, 1, 1, 0, 0, 0, 0]
    pred = [1, 1, 1, 0, 0, 0, 0, 1]
    kappa = compute_cohens_kappa(gold, pred)
    assert 0.4 < kappa < 0.9


def test_cohens_kappa_empty():
    assert compute_cohens_kappa([], []) == 0.0


def test_frr_and_har():
    assert compute_frr(2, 10) == 0.2
    assert compute_frr(0, 10) == 0.0
    assert compute_har(3, 10) == 0.3
    assert compute_har(0, 0) == 0.0


def test_compute_balanced_accuracy():
    # FRR = 0.0, HAR = 0.0 -> 100%
    assert compute_balanced_accuracy(0.0, 0.0) == 100.0
    # FRR = 0.2, HAR = 0.4 -> Benign fulfillment = 0.8, Harmful refusal = 0.6 -> (0.8 + 0.6) / 2 = 70.0%
    assert compute_balanced_accuracy(0.2, 0.4) == 70.0


def test_generate_pareto_points():
    pts = generate_pareto_points(base_frr=0.1, base_har=0.1)
    assert len(pts) == 9
    assert pts[0].refusal_threshold == 0.1
    assert pts[-1].refusal_threshold == 0.9
    for pt in pts:
        assert 0.0 <= pt.false_refusal_rate <= 1.0
        assert 0.0 <= pt.harmful_acceptance_rate <= 1.0
        assert 0.0 <= pt.balanced_f1 <= 1.0
