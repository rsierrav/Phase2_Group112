"""Configuration for the application."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # DynamoDB settings
    ARTIFACTS_TABLE_NAME: str = "Artifacts"
    AWS_REGION: str = "us-east-2"
    DYNAMODB_ENDPOINT_URL: str | None = None
    CREATE_TABLE: bool = False

    # API settings
    MAX_ARTIFACTS_PER_REQUEST: int = 100
    DEFAULT_PAGE_SIZE: int = 10


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
