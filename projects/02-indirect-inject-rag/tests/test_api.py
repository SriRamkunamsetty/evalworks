from fastapi.testclient import TestClient

from indirectinject.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "IndirectInject"}


def test_templates_endpoint():
    res = client.get("/api/v1/templates")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    assert any(t["id"] == "xml_override" for t in data)


def test_documents_ingest_and_chunks():
    payload = {
        "doc_name": "test_guide.txt",
        "content": "Paragraph 1\n\nParagraph 2",
        "poison_strategy": "xml_override",
    }
    res = client.post("/api/v1/documents/ingest", json=payload)
    assert res.status_code == 201
    assert res.json()["status"] == "ingested"

    res_chunks = client.get("/api/v1/documents/chunks")
    assert res_chunks.status_code == 200
    assert len(res_chunks.json()) > 0


def test_simulate_endpoint():
    payload = {
        "user_query": "What is the return policy?",
        "guardrail_mode": "strict",
        "top_k": 2,
    }
    res = client.post("/api/v1/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "simulation_id" in data
    assert data["guardrail_status"] in {"CONTAINED", "CLEAN", "HIJACKED"}


def test_static_files():
    assert client.get("/").status_code == 200
    assert client.get("/styles.css").status_code == 200
    assert client.get("/app.js").status_code == 200
