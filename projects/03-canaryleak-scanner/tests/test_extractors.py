import pytest

from canaryleak.engine.extractors import EXTRACTION_REGISTRY, get_probe, list_probes
from canaryleak.models import ExtractionTechnique


def test_list_probes_returns_all_techniques():
    probes = list_probes()
    assert len(probes) == 8
    techniques = {p.technique for p in probes}
    assert techniques == set(ExtractionTechnique)


def test_get_probe_success():
    for tech in ExtractionTechnique:
        probe = get_probe(tech)
        assert probe.technique == tech
        assert len(probe.name) > 0
        assert len(probe.prompt_text) > 0
        assert len(probe.description) > 0


def test_get_probe_invalid_raises():
    with pytest.raises(ValueError, match="Unknown extraction technique"):
        get_probe("non_existent_technique")  # type: ignore[arg-type]


def test_extraction_registry_integrity():
    for key, probe in EXTRACTION_REGISTRY.items():
        assert key == probe.technique
