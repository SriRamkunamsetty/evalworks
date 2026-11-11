from agenthijack.engine.probes import get_probe_by_category, list_probes
from agenthijack.models import AttackCategory


def test_list_probes():
    probes = list_probes()
    assert len(probes) == 8
    categories = {p.category for p in probes}
    assert categories == set(AttackCategory)


def test_get_probe_by_category():
    probe = get_probe_by_category(AttackCategory.SQL_INJECTION)
    assert probe is not None
    assert probe.target_tool == "run_sql_query"
    assert "Alice" in probe.prompt


def test_probe_attributes():
    for probe in list_probes():
        assert probe.probe_id.startswith("PROBE-")
        assert len(probe.name) > 0
        assert len(probe.prompt) > 0
        assert len(probe.description) > 0
        assert probe.target_tool in ["run_sql_query", "read_file", "fetch_url", "send_email"]
