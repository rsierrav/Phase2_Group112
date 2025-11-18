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

    # S3 settings
    S3_BUCKET_NAME: str = "ece461-artifacts"
    S3_ENDPOINT_URL: str | None = None  # For local development (e.g., LocalStack)
    AWS_ACCESS_KEY_ID: str | None = None  # Optional, will use IAM role if not set
    AWS_SECRET_ACCESS_KEY: str | None = None  # Optional, will use IAM role if not set

    # API settings
    MAX_ARTIFACTS_PER_REQUEST: int = 100
    DEFAULT_PAGE_SIZE: int = 10


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
