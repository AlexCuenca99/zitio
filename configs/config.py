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


class FirebaseSettings(BaseSettings):
    """Firebase settings, read from FIREBASE_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="FIREBASE_", env_file=ENV_FILE, extra="ignore")

    # host:port of the local Auth emulator. When set, ID tokens are verified against it.
    auth_emulator_host: str | None = None


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
    firebase: FirebaseSettings = Field(default_factory=FirebaseSettings)

    @field_validator("log_level")
    @classmethod
    def _uppercase(cls, v: str) -> str:
        """Normalize the log level to the uppercase names logging expects.

        Args:
            v: Log level as read from the environment.

        Returns:
            The log level in uppercase.
        """
        return v.upper()


settings = Settings()
