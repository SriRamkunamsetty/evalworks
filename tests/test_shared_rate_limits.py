from evalworks.config import settings


class FakeRedis:
    async def eval(self, script, key_count, key, ttl, limit, nonce):
        assert key_count == 1
        assert ttl == 60
        assert limit == 120
        assert len(nonce) == 32
        assert key.startswith("evalworks:rate:")
        return 121


def test_redis_rate_limit_is_shared_path_and_fails_closed(client, monkeypatch):
    from evalworks import security

    monkeypatch.setattr(settings, "redis_url", "rediss://cache.example.test/0")
    monkeypatch.setattr(security, "redis_client", lambda: FakeRedis())
    response = client.get("/health")
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"


def test_redis_failure_returns_service_unavailable(client, monkeypatch):
    from evalworks import security

    class BrokenRedis:
        async def eval(self, *args):
            raise ConnectionError("unavailable")

    monkeypatch.setattr(settings, "redis_url", "rediss://cache.example.test/0")
    monkeypatch.setattr(security, "redis_client", lambda: BrokenRedis())
    response = client.get("/health")
    assert response.status_code == 503
    assert "ConnectionError" not in response.text
