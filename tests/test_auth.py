"""This module defines the checks of Bearer token authentication on the API endpoints."""

import pytest
from firebase_admin import auth
from flask import Blueprint, g

from src.app.auth import token_required
from src.app.blueprints.v1.users import users_bp
from src.app.create_app import create_app
from src.infra.auth import firebase_auth
from src.interactor.errors import InternalError, UnauthenticatedError
from src.interactor.use_cases.users import UsersUseCase
from tests.fakes import (
    AUTHENTICATED_UID,
    EXPIRED_TOKEN,
    VALID_TOKEN,
    InMemoryUsersRepository,
    RecordingLogger,
    fake_verify_id_token,
)


def _client():
    """Build a test client over the users endpoints plus a protected probe route.

    Returns:
        The Flask test client, sending no Authorization header by default.
    """
    logger = RecordingLogger()
    probe = Blueprint("probe", __name__)

    @probe.get("/probe")
    @token_required
    def whoami():
        """Echo the authenticated uid.

        Returns:
            The uid ``token_required`` stored in ``flask.g``.
        """
        return {"uid": g.uid}

    app = create_app(
        [users_bp(UsersUseCase(InMemoryUsersRepository(), logger)), probe],
        logger,
        verify_id_token=fake_verify_id_token,
    )
    return app.test_client()


def _unauthenticated(response, code):
    """Assert that a response is a 401 with the expected code.

    Args:
        response: Response from the test client.
        code: Expected error code.

    Returns:
        The WWW-Authenticate header of the response.
    """
    assert response.status_code == 401, response.get_json()
    assert response.get_json()["error"]["code"] == code
    return response.headers.get("WWW-Authenticate")


@pytest.mark.parametrize(
    "header",
    [None, "Basic dXNlcjpwYXNz", "Bearer", "Bearer   ", VALID_TOKEN],
    ids=["missing", "basic-scheme", "bearer-without-token", "bearer-blank", "no-scheme"],
)
def test_missing_or_malformed_header_is_token_missing(header):
    """A request without a usable Bearer token answers 401 auth.token_missing.

    Args:
        header: Authorization header value, or None to send none.
    """
    headers = {"Authorization": header} if header is not None else {}
    challenge = _unauthenticated(_client().get("/probe", headers=headers), "auth.token_missing")
    assert challenge == "Bearer"


@pytest.mark.parametrize(
    ("token", "code"),
    [("forged-token", "auth.token_invalid"), (EXPIRED_TOKEN, "auth.token_expired")],
)
def test_rejected_token_signals_invalid_token(token, code):
    """An invalid or expired token answers 401 with its code and an invalid_token challenge.

    Args:
        token: Bearer token the fake verifier rejects.
        code: Expected error code.
    """
    response = _client().get("/probe", headers={"Authorization": f"Bearer {token}"})
    assert _unauthenticated(response, code) == 'Bearer error="invalid_token"'


@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER"])
def test_valid_token_exposes_the_uid(scheme):
    """A valid token reaches the view with its uid in flask.g, whatever the scheme case.

    Args:
        scheme: Spelling of the Bearer scheme.
    """
    response = _client().get("/probe", headers={"Authorization": f"{scheme} {VALID_TOKEN}"})
    assert response.status_code == 200
    assert response.get_json()["uid"] == AUTHENTICATED_UID


@pytest.mark.parametrize(
    ("method", "path"),
    [("post", "/api/v1/users"), ("get", "/api/v1/users"), ("get", "/api/v1/users/u1")],
)
def test_users_endpoints_require_a_token(method, path):
    """Every users endpoint answers 401 before running its logic when no token is sent.

    Args:
        method: HTTP method of the endpoint.
        path: URL of the endpoint.
    """
    response = getattr(_client(), method)(path, json={})
    _unauthenticated(response, "auth.token_missing")


@pytest.mark.parametrize(
    ("firebase_error", "expected"),
    [
        (auth.ExpiredIdTokenError("Token expired", cause=None), "auth.token_expired"),
        (auth.InvalidIdTokenError("Wrong audience"), "auth.token_invalid"),
    ],
)
def test_firebase_rejections_become_unauthenticated(monkeypatch, firebase_error, expected):
    """Firebase's token rejections map to their 401 codes, expired before invalid.

    Args:
        monkeypatch: Pytest fixture to replace the Firebase SDK call.
        firebase_error: Exception the SDK raises.
        expected: Expected error code.
    """

    def reject(token, app):
        """Raise the Firebase error under test.

        Args:
            token: ID token, unused.
            app: Firebase app, unused.

        Raises:
            FirebaseError: Always, the error under test.
        """
        raise firebase_error

    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: None)
    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", reject)

    with pytest.raises(UnauthenticatedError) as raised:
        firebase_auth.verify_id_token("any-token")
    assert raised.value.error_code == expected
    assert raised.value.status_code == 401


def test_unreachable_certificates_are_an_internal_error(monkeypatch):
    """Failing to fetch Google's certificates is our fault: 500, not 401.

    Args:
        monkeypatch: Pytest fixture to replace the Firebase SDK call.
    """

    def unreachable(token, app):
        """Raise the certificate fetch failure.

        Args:
            token: ID token, unused.
            app: Firebase app, unused.

        Raises:
            CertificateFetchError: Always.
        """
        raise auth.CertificateFetchError("Connection refused", cause=None)

    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: None)
    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", unreachable)

    with pytest.raises(InternalError) as raised:
        firebase_auth.verify_id_token("any-token")
    assert raised.value.error_code == "auth.internal_error"
    assert raised.value.status_code == 500


def test_verified_token_returns_its_uid(monkeypatch):
    """A token Firebase accepts yields the uid it carries.

    Args:
        monkeypatch: Pytest fixture to replace the Firebase SDK call.
    """
    monkeypatch.setattr(firebase_auth, "get_firebase_app", lambda: None)
    monkeypatch.setattr(
        firebase_auth.auth, "verify_id_token", lambda token, app: {"uid": "firebase-uid"}
    )

    assert firebase_auth.verify_id_token("any-token") == "firebase-uid"
