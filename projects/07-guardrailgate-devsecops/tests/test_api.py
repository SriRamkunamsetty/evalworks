from fastapi.testclient import TestClient

from guardrailgate.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "GuardrailGate"}


def test_api_suite():
    res = client.get("/api/v1/suite")
    assert res.status_code == 200
    suite = res.json()
    assert len(suite) == 10


def test_api_scan_hardened():
    payload = {
        "target_mode": "mock_hardened_ci",
        "baseline_safety_score": 95.0,
    }
    res = client.post("/api/v1/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["gate_verdict"] == "PASS"
    assert data["failed_tests"] == 0


def test_api_export_sarif():
    payload = {
        "target_mode": "mock_regressed_ci",
        "baseline_safety_score": 95.0,
    }
    scan_res = client.post("/api/v1/scan", json=payload)
    report_data = scan_res.json()

    sarif_res = client.post("/api/v1/export/sarif", json=report_data)
    assert sarif_res.status_code == 200
    assert sarif_res.json()["version"] == "2.1.0"


def test_web_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "GuardrailGate" in res.text
