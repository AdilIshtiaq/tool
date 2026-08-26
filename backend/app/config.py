from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://postgres@localhost:5432/nexcraft_salesos"

    n8n_base_url: str = "http://localhost:5678"

    google_places_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "NexCraft Solutions"

    imap_host: str = ""
    imap_port: int = 993

    api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
