from fastapi.testclient import TestClient

from crescendo.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "CrescendoSimulator"}


def test_api_scenarios():
    res = client.get("/api/v1/scenarios")
    assert res.status_code == 200
    scs = res.json()
    assert len(scs) == 3


def test_api_simulate():
    payload = {
        "scenario_id": "SCENARIO-01-REVERSE-ENGINEER",
        "target_mode": "hardened_adaptive_refusal",
    }
    res = client.post("/api/v1/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_turns_executed"] == 5
    assert data["multi_turn_breached"] is False


def test_web_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "CrescendoLab" in res.text
