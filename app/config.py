"""
config.py

@author: Emotu Balogun
@created: December 1, 2024

Configuration settings for the FastAPI application.

This module provides a centralized configuration management system using Pydantic BaseSettings.
It includes caching for performance optimization and environment variable support.
"""

from functools import lru_cache
from typing import Literal

from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .version import __version__ as api_version


class Settings(BaseSettings):
    """
    Settings class that manages all configuration variables for the application.

    Attributes:
        API_VERSION (str): Version of the API
        APP_NAME (str): Name of the application
        DESCRIPTION (str): Description of the application
        DATABASE_URL (str): Database connection string

    """

    API_VERSION: str = api_version
    API_NAME: str = "LLM Business Classifier"
    API_DESCRIPTION: str | None = "FastAPI application with Pydantic settings"

    BASE_URL: str = "http://localhost:8000"
    APP_LOGO: str = ""

    # Database
    DB_ECHO: bool = False
    DB_CONNECTION_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_NAME: str
    DATABASE_URL: str = ""
    VECTOR_STORE_URL: str = ""

    # Email
    RESEND_API_KEY: str
    RESEND_FROM_EMAIL: str = "noreply@resend.dev"
    ALLOW_EMAIL: Literal["on", "dev_only", "off"] = "dev_only"
    DEV_EMAIL: str = "emotu.balogun@gmail.com"

    # GCP
    GCP_PROJECT_ID: str
    GCP_PROJECT_LOCATION: str
    GCP_STORAGE_BUCKET: str

    # Vertex AI
    VERTEX_LLM_MODEL: str
    VERTEX_EMBEDDING_MODEL: str

    # OpenAI
    OPENAI_API_KEY: str | SecretStr
    OPENAI_LLM_MODEL: str
    OPENAI_EMBEDDING_MODEL: str

    LLM_PROVIDER: Literal["openai", "vertex"] = "openai"

    model_config = SettingsConfigDict(
        env_file=".env.local" if __debug__ else None,
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Creates and returns a cached instance of the Settings class.

    Returns:
        Settings: Application settings instance
    """
    _settings = Settings.model_validate({})
    _settings.DATABASE_URL = f"postgresql+asyncpg://{_settings.DB_USERNAME}:{_settings.DB_PASSWORD}@/{_settings.DB_NAME}?host={_settings.DB_CONNECTION_NAME}"
    _settings.VECTOR_STORE_URL = f"postgresql+psycopg://{_settings.DB_USERNAME}:{_settings.DB_PASSWORD}@/{_settings.DB_NAME}?host={_settings.DB_CONNECTION_NAME}"
    return _settings


settings = get_settings()
