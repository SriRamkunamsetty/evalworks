from fastapi.testclient import TestClient

from owaspbench.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "OWASPTop10Bench"}


def test_api_categories():
    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    cats = res.json()
    assert len(cats) == 10


def test_api_dataset():
    res = client.get("/api/v1/dataset")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 30


def test_api_benchmark():
    payload = {
        "target_mode": "hardened_grade_a",
        "categories": ["LLM01:Prompt_Injection"],
    }
    res = client.post("/api/v1/benchmark", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_evaluations"] == 3
    assert data["passed_evaluations"] == 3
    assert data["overall_letter_grade"] in ["A", "A+"]


def test_web_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "OWASP LLM Benchmark" in res.text
