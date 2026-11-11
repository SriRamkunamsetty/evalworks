from fastapi.testclient import TestClient

from calibrator.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "SafetyRubricCalibrator"}


def test_api_pairs():
    res = client.get("/api/v1/pairs")
    assert res.status_code == 200
    pairs = res.json()
    assert len(pairs) == 8


def test_api_calibrate():
    payload = {"target_mode": "well_calibrated_optimal"}
    res = client.post("/api/v1/calibrate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_contrast_pairs"] == 8
    assert data["cohens_kappa"] == 1.0


def test_web_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "SafetyCalibrator" in res.text
