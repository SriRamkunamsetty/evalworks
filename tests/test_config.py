import pytest

from evalworks.config import settings, validate_production_settings


def test_production_rejects_development_secret_and_sqlite(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", "local-dev-key-change-me")
    monkeypatch.setattr(settings, "database_url", "sqlite:///./evalworks.db")
    with pytest.raises(RuntimeError, match="API_KEY"):
        validate_production_settings()


def test_production_requires_tls_for_external_model_provider(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", "secure-random-key-of-at-least-thirty-two-chars")
    monkeypatch.setattr(settings, "session_secret", "a" * 48)
    monkeypatch.setattr(settings, "data_encryption_key", "b" * 48)
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "redis_url", "rediss://cache.test:6380/0")
    monkeypatch.setattr(
        settings, "database_url", "postgresql+psycopg://user:pass@db.test/evalworks"
    )
    monkeypatch.setattr(settings, "llm_base_url", "http://provider.example/v1")
    with pytest.raises(RuntimeError, match="HTTPS"):
        validate_production_settings()


def test_production_requires_distinct_session_secret(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", "secure-random-key-of-at-least-thirty-two-chars")
    monkeypatch.setattr(settings, "session_secret", settings.api_key)
    monkeypatch.setattr(settings, "data_encryption_key", "b" * 48)
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "redis_url", "rediss://cache.test:6380/0")
    monkeypatch.setattr(
        settings, "database_url", "postgresql+psycopg://user:pass@db.test/evalworks"
    )
    monkeypatch.setattr(settings, "llm_base_url", "")
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        validate_production_settings()
