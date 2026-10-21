from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "INVIX Catalog API"
    app_env: Literal["development", "test", "production"] = "development"

    database_url: SecretStr = SecretStr(
        "postgresql://invix:invix_dev_password@localhost:5432/invix"
    )

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "invix_local"
    minio_secret_key: SecretStr = SecretStr("invix_dev_minio_password")
    minio_bucket: str = "product-photos"
    minio_secure: bool = False

    web_app_url: str = "http://localhost:3000"
    bot_token: SecretStr = SecretStr("")
    demo_admin_code: SecretStr = SecretStr("")
    telegram_webhook_secret: SecretStr = SecretStr("")
    telegram_auth_max_age: int = 3600
    max_photo_bytes: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
