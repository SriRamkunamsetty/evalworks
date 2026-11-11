import pytest

from visionjailbreak.generator.probes import get_vision_probe, list_vision_probes


def test_list_vision_probes():
    probes = list_vision_probes()
    assert len(probes) == 6
    ids = {p.probe_id for p in probes}
    assert "VIS-01" in ids
    assert "VIS-06" in ids


def test_get_vision_probe_valid():
    probe = get_vision_probe("VIS-01")
    assert probe.probe_id == "VIS-01"
    assert "TYPOGRAPHIC_OVERRIDE_CONFIRMED" in probe.forbidden_signature


def test_get_vision_probe_invalid():
    with pytest.raises(KeyError, match="Unknown vision probe"):
        get_vision_probe("NON_EXISTENT")
