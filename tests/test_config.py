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
    monkeypatch.setattr(settings, "data_hmac_key", "different-random-data-hmac-key-at-least-32")
    monkeypatch.setattr(settings, "session_secret", "a" * 48)
    monkeypatch.setattr(settings, "cookie_secure", True)
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
    monkeypatch.setattr(settings, "data_hmac_key", "different-random-data-hmac-key-at-least-32")
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(
        settings, "database_url", "postgresql+psycopg://user:pass@db.test/evalworks"
    )
    monkeypatch.setattr(settings, "llm_base_url", "")
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        validate_production_settings()


def test_production_requires_distinct_data_fingerprint_key(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", "secure-random-key-of-at-least-thirty-two-chars")
    monkeypatch.setattr(
        settings, "session_secret", "different-session-secret-at-least-32-characters"
    )
    monkeypatch.setattr(settings, "data_hmac_key", settings.session_secret)
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://db.test/evalworks")
    monkeypatch.setattr(settings, "llm_base_url", "")
    with pytest.raises(RuntimeError, match="DATA_HMAC_KEY"):
        validate_production_settings()


def test_production_model_endpoint_requires_allowlisted_public_hostname(monkeypatch):
    import socket

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", "secure-random-key-of-at-least-thirty-two-chars")
    monkeypatch.setattr(
        settings, "session_secret", "different-session-secret-at-least-32-characters"
    )
    monkeypatch.setattr(settings, "data_hmac_key", "separate-data-fingerprint-key-minimum-32")
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://db.test/evalworks")
    monkeypatch.setattr(settings, "llm_base_url", "https://provider.example/v1")
    monkeypatch.setattr(settings, "llm_allowed_hosts", "provider.example")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("93.184.216.34", 443))],
    )
    validate_production_settings()
    monkeypatch.setattr(settings, "llm_allowed_hosts", "other.example")
    with pytest.raises(RuntimeError, match="LLM_ALLOWED_HOSTS"):
        validate_production_settings()
    monkeypatch.setattr(settings, "llm_allowed_hosts", "provider.example")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("127.0.0.1", 443))],
    )
    with pytest.raises(RuntimeError, match="public addresses"):
        validate_production_settings()
