from __future__ import annotations

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://elnuser:elnpass@db:5432/elndb"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    UPLOAD_DIR: str = "/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        """Auto-normalize postgresql:// → postgresql+psycopg://"""
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg://", 1)
        return v


settings = Settings()
