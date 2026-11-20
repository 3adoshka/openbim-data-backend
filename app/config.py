from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./openbim.db"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str | None = None
    minio_access_key: str = "openbim"
    minio_secret_key: str = "openbim-secret"
    minio_bucket: str = "openbim-models"
    local_storage_dir: str = ".storage"

settings = Settings()
