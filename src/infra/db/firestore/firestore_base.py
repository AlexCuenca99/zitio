"""This module defines base classes for Firestore connections."""

# Third-parties
from google.cloud import firestore

# Locals
from configs import config


def _build_firestore_client():
    """
    Build a Firestore client using credentials and project configuration.
    """
    return firestore.Client(project=config.GCP_PROJECT_ID)


firestore_client = _build_firestore_client()


class BaseFirestoreRepository:
    """Base class for Firestore repositories."""

    def __init__(self, firestore_client=firestore_client):
        self.firestore = firestore_client

    def health_check(self) -> bool:
        """Check if Firestore connection is alive."""
        try:
            # Small metadata query to validate the client.
            list(self.firestore.collections())
            return True
        except Exception:
            return False
