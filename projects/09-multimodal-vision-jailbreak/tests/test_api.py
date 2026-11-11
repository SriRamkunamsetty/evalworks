from fastapi.testclient import TestClient

from visionjailbreak.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "MultimodalVisionJailbreak"}


def test_api_probes():
    res = client.get("/api/v1/probes")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 6


def test_api_generate_image():
    payload = {"text": "TEST_PREVIEW", "perturbation": "plain_typographic"}
    res = client.post("/api/v1/generate-image", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["image_base64"]) > 100


def test_api_audit_hardened():
    payload = {
        "probe_ids": ["VIS-01"],
        "target_mode": "vlm_hardened_ocr_guard",
    }
    res = client.post("/api/v1/audit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["breaches_count"] == 0
    assert data["multimodal_robustness_score"] == 100.0


def test_web_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "VisionJailbreak" in res.text
