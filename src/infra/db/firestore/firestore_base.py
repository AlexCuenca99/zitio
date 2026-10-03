"""This module defines the Firestore client factory."""

# Natives
import os
from functools import cache

# Third-parties
from google.cloud import firestore
from google.oauth2 import service_account

# Locals
from configs.config import settings


@cache
def get_firestore_client() -> firestore.Client:
    """
    Return the process-wide Firestore client, built on first use.

    pydantic-settings reads the .env file without exporting it, so the emulator host and the
    credentials file are handed to the SDK here instead of relying on os.environ.
    """
    if settings.firestore.emulator_host:
        # The SDK only detects the emulator through this variable; it uses anonymous credentials.
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore.emulator_host
        return firestore.Client(project=settings.project_id)

    credentials = None
    if settings.google_application_credentials:
        credentials = service_account.Credentials.from_service_account_file(
            settings.google_application_credentials
        )

    return firestore.Client(project=settings.project_id, credentials=credentials)
