"""This module defines the checks of the authenticated user's profile endpoints."""

import pytest

from src.app.blueprints.v1.users import users_bp
from src.app.create_app import create_app
from src.interactor.use_cases.users import UsersUseCase
from tests.fakes import (
    AUTHENTICATED_EMAIL,
    AUTHENTICATED_UID,
    NO_EMAIL_TOKEN,
    VALID_TOKEN,
    InMemoryUsersRepository,
    RecordingLogger,
    fake_verify_id_token,
)

ME = "/api/v1/users/me"
AUTH = {"Authorization": f"Bearer {VALID_TOKEN}"}


def _client():
    """Build a test client over the users endpoints with an empty repository.

    Returns:
        The Flask test client.
    """
    logger = RecordingLogger()
    app = create_app(
        [users_bp(UsersUseCase(InMemoryUsersRepository(), logger))],
        logger,
        verify_id_token=fake_verify_id_token,
    )
    return app.test_client()


def _create(client, **fields):
    """Create the caller's profile.

    Args:
        client: Flask test client.
        **fields: Profile fields to send; display_name defaults to "Ana".

    Returns:
        The response of the create request.
    """
    return client.post(ME, headers=AUTH, json={"display_name": "Ana", **fields})


def _error_code(response):
    """Read the error code of an error response.

    Args:
        response: Response from the test client.

    Returns:
        The ``error.code`` of the body.
    """
    return response.get_json()["error"]["code"]


def test_create_takes_identity_from_the_token():
    """The profile gets uid and email from the token and always starts as driver."""
    response = _create(_client(), phone=" 0991234567 ", vehicle_plate="abc-1234")

    assert response.status_code == 201
    profile = response.get_json()["data"]
    assert profile["uid"] == AUTHENTICATED_UID
    assert profile["email"] == AUTHENTICATED_EMAIL
    assert profile["role"] == "driver"
    assert profile["phone"] == "0991234567"
    assert profile["vehicle_plate"] == "ABC-1234"


@pytest.mark.parametrize(
    "field",
    [
        {"uid": "someone-else"},
        {"email": "other@zitio.com"},
        {"role": "owner"},
        {"is_active": False},
        {"history_summary": {"total_bookings": 99}},
    ],
    ids=["uid", "email", "role", "is_active", "history_summary"],
)
def test_create_rejects_fields_the_client_does_not_own(field):
    """Identity, role and system fields in the body answer 400 instead of being used.

    Args:
        field: Forbidden field sent with an otherwise valid body.
    """
    response = _create(_client(), **field)

    assert response.status_code == 400
    assert _error_code(response) == "request.param_invalid"
    assert response.get_json()["error"]["param"] == next(iter(field))


def test_create_twice_is_a_conflict():
    """Creating an existing profile answers 409 users.already_exists, not an overwrite."""
    client = _client()
    _create(client)

    response = _create(client, display_name="Impostor")

    assert response.status_code == 409
    assert _error_code(response) == "users.already_exists"
    assert client.get(ME, headers=AUTH).get_json()["data"]["display_name"] == "Ana"


def test_create_without_email_in_the_token_is_param_required():
    """Accounts without email cannot create a profile: 400 users.param_required."""
    response = _client().post(
        ME, headers={"Authorization": f"Bearer {NO_EMAIL_TOKEN}"}, json={"display_name": "Ana"}
    )

    assert response.status_code == 400
    assert _error_code(response) == "users.param_required"
    assert response.get_json()["error"]["param"] == "email"


def test_get_returns_the_created_profile():
    """GET /me returns the profile created by the same token."""
    client = _client()
    created = _create(client).get_json()["data"]

    response = client.get(ME, headers=AUTH)

    assert response.status_code == 200
    assert response.get_json()["data"] == created


def test_get_before_creating_is_not_found():
    """GET /me without a profile answers 404 users.not_found, so the app knows to create it."""
    response = _client().get(ME, headers=AUTH)

    assert response.status_code == 404
    assert _error_code(response) == "users.not_found"


def test_patch_updates_only_the_sent_fields():
    """PATCH /me changes the sent fields, keeps the rest and refreshes updated_at."""
    client = _client()
    created = _create(client, phone="0991234567").get_json()["data"]

    response = client.patch(ME, headers=AUTH, json={"vehicle_plate": "xyz-9876"})

    assert response.status_code == 200
    updated = response.get_json()["data"]
    assert updated["vehicle_plate"] == "XYZ-9876"
    assert updated["phone"] == "0991234567"
    assert updated["display_name"] == "Ana"
    assert updated["updated_at"] > created["updated_at"]
    assert client.get(ME, headers=AUTH).get_json()["data"] == updated


@pytest.mark.parametrize(
    "field",
    [{"role": "owner"}, {"email": "other@zitio.com"}, {"uid": "someone-else"}],
    ids=["role", "email", "uid"],
)
def test_patch_rejects_fields_that_are_not_editable(field):
    """Changing role, email or uid answers 400 and leaves the profile untouched.

    Args:
        field: Non-editable field sent in the update.
    """
    client = _client()
    created = _create(client).get_json()["data"]

    response = client.patch(ME, headers=AUTH, json=field)

    assert response.status_code == 400
    assert _error_code(response) == "request.param_invalid"
    assert client.get(ME, headers=AUTH).get_json()["data"] == created


def test_patch_rejects_invalid_values():
    """A value the entity rejects (blank display name) answers 400 request.param_invalid."""
    client = _client()
    _create(client)

    response = client.patch(ME, headers=AUTH, json={"display_name": "   "})

    assert response.status_code == 400
    assert _error_code(response) == "request.param_invalid"


def test_patch_before_creating_is_not_found():
    """PATCH /me without a profile answers 404 users.not_found."""
    response = _client().patch(ME, headers=AUTH, json={"phone": "0991234567"})

    assert response.status_code == 404
    assert _error_code(response) == "users.not_found"


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/v1/users"), ("get", f"/api/v1/users/{AUTHENTICATED_UID}")],
    ids=["list", "by-uid"],
)
def test_removed_endpoints_no_longer_exist(method, path):
    """The open user list and the lookup by uid were removed.

    Args:
        method: HTTP method of the removed endpoint.
        path: URL of the removed endpoint.
    """
    response = getattr(_client(), method)(path, headers=AUTH)

    assert response.status_code == 404
    assert _error_code(response) == "http.not_found"
