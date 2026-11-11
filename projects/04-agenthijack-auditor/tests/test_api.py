from fastapi.testclient import TestClient

from agenthijack.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "AgentHijackAuditor"}


def test_api_tools():
    res = client.get("/api/v1/tools")
    assert res.status_code == 200
    tools = res.json()
    assert len(tools) == 4
    names = [t["name"] for t in tools]
    assert "run_sql_query" in names
    assert "fetch_url" in names


def test_api_probes():
    res = client.get("/api/v1/probes")
    assert res.status_code == 200
    probes = res.json()
    assert len(probes) == 8


def test_api_audit_endpoint():
    payload = {
        "agent_system_instructions": "You are a customer service assistant.",
        "policy_mode": "strict_least_privilege",
        "categories": ["sql_injection", "path_traversal"],
        "target_mode": "mock_hardened",
    }
    res = client.post("/api/v1/audit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_probes"] == 2
    assert data["confirmed_violations"] == 0


def test_api_simulate_tool():
    payload = {
        "tool_call": {
            "tool_name": "read_file",
            "arguments": {"path": "public/faq.txt"},
        },
        "policy_mode": "strict_least_privilege",
    }
    res = client.post("/api/v1/simulate-tool", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True


def test_web_static_index():
    res = client.get("/")
    assert res.status_code == 200
    assert "AgentHijack Auditor" in res.text
