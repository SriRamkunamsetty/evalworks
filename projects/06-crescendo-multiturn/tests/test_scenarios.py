import pytest

from crescendo.engine.scenarios import get_scenario, list_scenarios
from crescendo.models import EscalationStage


def test_list_scenarios():
    scenarios = list_scenarios()
    assert len(scenarios) == 3
    ids = {s.scenario_id for s in scenarios}
    assert "SCENARIO-01-REVERSE-ENGINEER" in ids
    assert "SCENARIO-02-SANDBOX-EVASION" in ids
    assert "SCENARIO-03-CREDENTIAL-DISCOVERY" in ids


def test_get_scenario_success():
    sc = get_scenario("SCENARIO-01-REVERSE-ENGINEER")
    assert sc.title == "Proprietary Ranking Algorithm Exfiltration"
    assert len(sc.prompts_by_stage) == len(EscalationStage)
    for stage in EscalationStage:
        assert stage in sc.prompts_by_stage


def test_get_scenario_invalid_raises():
    with pytest.raises(KeyError, match="Unknown Crescendo scenario"):
        get_scenario("NON-EXISTENT-SCENARIO")
