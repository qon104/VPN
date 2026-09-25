from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "VPN Subscription Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    KEY_HMAC_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Bot
    BOT_API_SECRET: str

    # Payments
    PAYMENT_PROVIDER: str = "telegram_stars"
    PAYMENT_WEBHOOK_SECRET: str = ""

    # Download
    DOWNLOAD_BASE_URL: str = "https://yourdomain.com/downloads"
    DOWNLOAD_TOKEN_EXPIRE_HOURS: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()