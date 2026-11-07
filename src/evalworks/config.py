from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "EvalWorks"
    database_url: str = "sqlite:///./.data/evalworks.db"
    api_key: str = "local-dev-key-change-me"
    max_request_bytes: int = 65_536
    allowed_origins: str = "http://localhost:8000"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""


settings = Settings()


def validate_production_settings() -> None:
    if settings.app_env.lower() == "production":
        if len(settings.api_key) < 32 or settings.api_key == "local-dev-key-change-me":
            raise RuntimeError("Production requires a unique API_KEY of at least 32 characters")
        if settings.database_url.startswith("sqlite"):
            raise RuntimeError(
                "Production requires a managed database; SQLite is for local use only"
            )
        if settings.llm_base_url:
            parsed = urlparse(settings.llm_base_url)
            if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
                raise RuntimeError("Production LLM_BASE_URL must use HTTPS")
