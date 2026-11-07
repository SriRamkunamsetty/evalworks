import ipaddress
import socket
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "EvalWorks"
    database_url: str = "sqlite:///./.data/evalworks.db"
    api_key: str = "local-dev-key-change-me"
    data_hmac_key: str = ""
    session_secret: str = "development-secret-change-before-deploying-32-chars-minimum"
    data_encryption_key: str = "development-data-encryption-key-change-before-deploying"
    cookie_secure: bool = False
    redis_url: str = ""
    max_request_bytes: int = 65_536
    allowed_origins: str = "http://localhost:8000"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_allowed_hosts: str = ""


settings = Settings()


def validate_production_settings() -> None:
    if settings.app_env.lower() == "production":
        if len(settings.api_key) < 32 or settings.api_key == "local-dev-key-change-me":
            raise RuntimeError("Production requires a unique API_KEY of at least 32 characters")
        if (
            len(settings.session_secret) < 32
            or settings.session_secret.startswith("development-")
            or settings.session_secret == settings.api_key
        ):
            raise RuntimeError(
                "Production requires a unique SESSION_SECRET of at least 32 characters"
            )
        if (
            len(settings.data_encryption_key) < 32
            or settings.data_encryption_key.startswith("development-")
            or settings.data_encryption_key
            in {settings.api_key, settings.session_secret, settings.data_hmac_key}
        ):
            raise RuntimeError(
                "Production requires a unique DATA_ENCRYPTION_KEY of at least 32 characters"
            )
        if not settings.redis_url.startswith("rediss://"):
            raise RuntimeError("Production requires a TLS protected REDIS_URL using rediss://")
        if not settings.cookie_secure:
            raise RuntimeError("Production requires COOKIE_SECURE=true")
        if len(settings.data_hmac_key) < 32 or settings.data_hmac_key in {
            settings.api_key,
            settings.session_secret,
            settings.data_encryption_key,
        }:
            raise RuntimeError(
                "Production requires a separate DATA_HMAC_KEY of at least 32 characters"
            )
        if settings.database_url.startswith("sqlite"):
            raise RuntimeError(
                "Production requires a managed database; SQLite is for local use only"
            )
        if settings.llm_base_url:
            parsed = urlparse(settings.llm_base_url)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise RuntimeError("Production LLM_BASE_URL must use HTTPS")
            allowed_hosts = {
                host.strip().lower()
                for host in settings.llm_allowed_hosts.split(",")
                if host.strip()
            }
            hostname = parsed.hostname.lower()
            if hostname not in allowed_hosts:
                raise RuntimeError("Production LLM endpoint hostname must be in LLM_ALLOWED_HOSTS")
            try:
                addresses = {
                    entry[4][0] for entry in socket.getaddrinfo(hostname, parsed.port or 443)
                }
                if not addresses or any(
                    not ipaddress.ip_address(address).is_global for address in addresses
                ):
                    raise RuntimeError("Production LLM endpoint must resolve to public addresses")
            except (OSError, ValueError):
                raise RuntimeError("Production LLM endpoint could not be safely resolved") from None
