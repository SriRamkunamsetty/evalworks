from crescendo.engine.simulator import CrescendoSimulator
from crescendo.models import CrescendoAuditRequest


def test_simulator_hardened_target_passes():
    sim = CrescendoSimulator()
    req = CrescendoAuditRequest(
        scenario_id="SCENARIO-01-REVERSE-ENGINEER",
        target_mode="hardened_adaptive_refusal",
    )
    report = sim.run_simulation(req)
    assert report.total_turns_executed == 5
    assert report.multi_turn_breached is False
    assert report.turn_of_failure is None
    assert report.crescendo_amplification_factor == 0.0
    assert "ROBUST RESISTANCE" in report.executive_summary


def test_simulator_vulnerable_target_demonstrates_crescendo():
    sim = CrescendoSimulator()
    req = CrescendoAuditRequest(
        scenario_id="SCENARIO-01-REVERSE-ENGINEER",
        target_mode="leaky_crescendo_vulnerable",
    )
    report = sim.run_simulation(req)
    assert report.total_turns_executed == 5
    # Demonstrates asymmetric Crescendo vulnerability
    assert report.single_turn_breached is False
    assert report.multi_turn_breached is True
    assert report.turn_of_failure == 5
    assert report.crescendo_amplification_factor == 5.0
    assert "ASYMMETRIC CRESCENDO VULNERABILITY" in report.executive_summary
