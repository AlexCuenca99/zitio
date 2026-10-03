"""This module defines the verification of Firebase Authentication ID tokens."""

# Natives
import os
from functools import cache

# Third-parties
import firebase_admin
from firebase_admin import auth, credentials

# Locals
from configs.config import settings
from src.interactor.errors import InternalError, UnauthenticatedError


@cache
def get_firebase_app() -> firebase_admin.App:
    """Return the process-wide Firebase app, initialized on first use.

    pydantic-settings reads the .env file without exporting it, so the emulator host and
    the credentials file are handed to the SDK here instead of relying on os.environ.

    Returns:
        The default Firebase app for the configured project.
    """
    options = {"projectId": settings.project_id}

    if settings.firebase.auth_emulator_host:
        # The SDK only detects the emulator through this variable; tokens are not signed there.
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.firebase.auth_emulator_host
        return firebase_admin.initialize_app(options=options)

    credential = None
    if settings.google_application_credentials:
        credential = credentials.Certificate(settings.google_application_credentials)

    # Without a credential the SDK uses Application Default Credentials (Cloud Run).
    return firebase_admin.initialize_app(credential=credential, options=options)


def verify_id_token(token: str) -> dict:
    """Verify a Firebase ID token and return the identity it carries.

    Args:
        token: Firebase ID token sent by the client as a Bearer token.

    Returns:
        The authenticated identity: ``{"uid": ..., "email": ...}``. ``email`` is None for
        accounts without one (e.g. phone or anonymous sign-in).

    Raises:
        UnauthenticatedError: If the token is expired ("auth.token_expired") or invalid
            ("auth.token_invalid").
        InternalError: If the token could not be checked, e.g. Google's certificates are
            unreachable ("auth.internal_error").
    """
    try:
        decoded = auth.verify_id_token(token, app=get_firebase_app())
    # ExpiredIdTokenError subclasses InvalidIdTokenError, so it must be caught first.
    except auth.ExpiredIdTokenError as error:
        raise UnauthenticatedError("auth.token_expired", message=str(error)) from error
    except auth.InvalidIdTokenError as error:
        raise UnauthenticatedError("auth.token_invalid", message=str(error)) from error
    except auth.CertificateFetchError as error:
        raise InternalError("auth.internal_error", message=str(error)) from error

    return {"uid": decoded["uid"], "email": decoded.get("email")}
