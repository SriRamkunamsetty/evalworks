from calibrator.dataset.pairs import list_contrast_pairs


def test_list_contrast_pairs():
    pairs = list_contrast_pairs()
    assert len(pairs) == 8
    domains = {p.domain for p in pairs}
    assert "Database Administration" in domains
    assert "Operating System Security" in domains
    assert "Web Application Architecture" in domains


def test_contrast_pair_structure():
    for pair in list_contrast_pairs():
        assert pair.pair_id.startswith("PAIR-")
        assert len(pair.benign_prompt) > 0
        assert len(pair.adversarial_prompt) > 0
        assert len(pair.adversarial_forbidden_tokens) > 0
        assert len(pair.description) > 0
