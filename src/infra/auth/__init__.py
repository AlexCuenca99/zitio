"""This module defines the public API of the auth infrastructure package."""

from .firebase_auth import get_firebase_app, verify_id_token

__all__ = ["get_firebase_app", "verify_id_token"]
