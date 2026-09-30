"""This module defines the runtime settings read from the environment."""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.constants import DEVELOPMENT_ENVIRONMENT

BASE_DIR = Path(__file__).resolve().parent.parent

# Local runs (IDE, scripts) read the compose .env. Missing files are ignored, so Cloud Run
# relies on real environment variables only, which always win over the file.
ENV_FILE = BASE_DIR / "docker" / "local" / "prod" / ".env"


class FirestoreSettings(BaseSettings):
    """Firestore settings, read from FIRESTORE_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="FIRESTORE_", env_file=ENV_FILE, extra="ignore")

    # host:port of the local emulator. When set, the client skips real credentials.
    emulator_host: str | None = None


class Settings(BaseSettings):
    """Settings read from the environment once at instantiation."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    environment: str = DEVELOPMENT_ENVIRONMENT
    log_level: str = "INFO"
    show_traceback: bool = False
    service_name: str = "zitio"
    project_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    google_application_credentials: str | None = None

    flask_debug: bool = False
    flask_host: str = "127.0.0.1"

    firestore: FirestoreSettings = Field(default_factory=FirestoreSettings)

    @field_validator("log_level")
    @classmethod
    def _uppercase(cls, v: str) -> str:
        return v.upper()


settings = Settings()
