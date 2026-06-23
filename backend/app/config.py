"""
config.py — Application settings loaded from environment variables.
Uses pydantic-settings for type-safe config with .env file support.

Production secrets are loaded from GCP Secret Manager (injected as env vars).
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongo_uri: str = Field(..., env="MONGO_URI")
    mongo_db_name: str = Field("whatsapp_agent", env="MONGO_DB_NAME")

    # ── Google Gemini ─────────────────────────────────────────────────────────
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    # ── Twilio WhatsApp ───────────────────────────────────────────────────────
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")

    # Twilio WhatsApp sandbox number (used for both tenants during testing)
    # Format: "whatsapp:+14155238886"
    twilio_whatsapp_number_tenant_a: str = Field(
        "whatsapp:+14155238886", env="TWILIO_WHATSAPP_NUMBER_TENANT_A"
    )
    twilio_whatsapp_number_tenant_b: str = Field(
        "whatsapp:+14155238886", env="TWILIO_WHATSAPP_NUMBER_TENANT_B"
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = Field("development", env="APP_ENV")
    cors_origins: str = Field("http://localhost:5173", env="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — reads .env once at startup."""
    return Settings()
