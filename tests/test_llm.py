import json

from evalworks import llm


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.body


def configure_provider(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_base_url", "https://models.example.test/v1")
    monkeypatch.setattr(llm.settings, "llm_api_key", "unit-test-secret")
    monkeypatch.setattr(llm.settings, "llm_model", "test-model")


def test_chat_provider_returns_answer_without_saving_input(monkeypatch):
    configure_provider(monkeypatch)
    monkeypatch.setattr(
        llm.urllib.request,
        "urlopen",
        lambda _request, timeout: FakeResponse(
            {"model": "test-model", "choices": [{"message": {"content": "A test answer"}}]}
        ),
    )
    result = llm.chat([{"role": "user", "content": "private prompt"}])
    assert result["content"] == "A test answer"
    assert result["latency_ms"] >= 0
    assert "private prompt" not in json.dumps(result)


def test_probe_agent_requests_json_and_returns_reviewable_drafts(monkeypatch):
    configure_provider(monkeypatch)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data)
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "cases": [
                                        {
                                            "prompt": "Clarify the request",
                                            "risk_hypothesis": "ambiguity",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    cases = llm.propose_probe_cases("Test ambiguity handling", 2)
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert cases[0]["prompt"] == "Clarify the request"
