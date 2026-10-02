"""This module defines the checks that every API error shares one body, status and code."""

import re
from pathlib import Path

from flask import Blueprint, abort

from src.app.blueprints.v1.users import users_bp
from src.app.create_app import create_app
from src.interactor.errors import (
    ERROR_CATALOG,
    InternalError,
    NotFoundError,
    ParamRequiredError,
)
from src.interactor.use_cases.users import UsersUseCase

SRC_DIR = Path(__file__).resolve().parent.parent / "src"


class InMemoryUsersRepository:
    """Users repository kept in memory, so the checks need no Firestore."""

    def __init__(self):
        """Start with no users."""
        self.users = {}

    def create(self, user):
        """Store a user.

        Args:
            user: User entity to store.

        Returns:
            The stored user.
        """
        self.users[user.uid] = user
        return user

    def get_by_uid(self, uid):
        """Get a user by uid.

        Args:
            uid: Identifier of the user.

        Returns:
            The user, or None when it does not exist.
        """
        return self.users.get(uid)

    def list_all(self):
        """List every stored user.

        Returns:
            The stored users.
        """
        return list(self.users.values())


class RecordingLogger:
    """Logger that records which level and message every call used."""

    def __init__(self):
        """Start with no recorded calls."""
        self.calls = []

    def extract_trace_id_from_request(self):
        """Return a fixed trace id.

        Returns:
            The trace id every response must carry as request_id.
        """
        return "trace-123"

    def __getattr__(self, level):
        """Record any log_* call instead of logging it.

        Args:
            level: Name of the logger method called (e.g. "log_warning").

        Returns:
            A function that records ``(level, message)``.
        """
        return lambda message, **context: self.calls.append((level, message))


def _client():
    """Build a test client over the users endpoints plus routes that always fail.

    Returns:
        The Flask test client and the logger recording its calls.
    """
    logger = RecordingLogger()
    boom = Blueprint("boom", __name__)

    @boom.get("/boom")
    def explode():
        """Fail with an unexpected exception.

        Raises:
            RuntimeError: Always, with a detail that must not reach the client.
        """
        raise RuntimeError("secret internal detail")

    @boom.get("/abort/<int:status_code>")
    def abort_with(status_code):
        """Abort with the given HTTP status, as werkzeug does on its own.

        Args:
            status_code: HTTP status to abort with.

        Raises:
            HTTPException: Always, for the given status.
        """
        abort(status_code)

    app = create_app([users_bp(UsersUseCase(InMemoryUsersRepository(), logger)), boom], logger)
    return app.test_client(), logger


def _error(response, status_code, code):
    """Assert that a response is an API error with the expected status and code.

    Args:
        response: Response from the test client.
        status_code: Expected HTTP status code.
        code: Expected error code.

    Returns:
        The ``error`` object of the body, for further checks.
    """
    assert response.status_code == status_code, (response.status_code, response.get_json())
    body = response.get_json()
    assert body["status"] == "fail"
    assert set(body["error"]) == {"type", "code", "message", "param", "details", "request_id"}
    assert body["error"]["code"] == code, body
    assert body["error"]["request_id"] == "trace-123"
    return body["error"]


def test_missing_field_is_param_required():
    """A missing field answers 400 request.param_required naming the field."""
    client, _ = _client()
    error = _error(
        client.post("/api/v1/users", json={"uid": "u1", "email": "a@b.co", "role": "driver"}),
        400,
        "request.param_required",
    )
    assert error["param"] == "display_name"


def test_invalid_field_is_param_invalid_without_echoing_input():
    """A malformed field answers 400 request.param_invalid without echoing the input."""
    client, _ = _client()
    payload = {"uid": "u1", "display_name": "Alex", "email": "not-an-email", "role": "driver"}
    error = _error(client.post("/api/v1/users", json=payload), 400, "request.param_invalid")
    assert error["param"] == "email"
    assert "not-an-email" not in str(error)


def test_body_that_is_not_an_object_names_the_body():
    """A JSON list or null as body answers request.param_invalid with param "body"."""
    client, _ = _client()
    for body in ("[]", "null"):
        response = client.post("/api/v1/users", data=body, content_type="application/json")
        error = _error(response, 400, "request.param_invalid")
        assert error["param"] == "body"
        assert error["message"] == "El parámetro /body/ es inválido."


def test_unmapped_http_errors_answer_in_spanish():
    """HTTP errors without a specific message fall back to a generic Spanish one."""
    client, _ = _client()
    cases = (
        (422, "http.unprocessable_entity", "La solicitud no es válida."),
        (503, "http.service_unavailable", "Ocurrió un error interno."),
    )
    for status_code, code, message in cases:
        error = _error(client.get(f"/abort/{status_code}"), status_code, code)
        assert error["message"] == message, status_code


def test_malformed_json_is_bad_request():
    """A body that is not JSON answers 400 http.bad_request."""
    client, _ = _client()
    response = client.post("/api/v1/users", data="{bad", content_type="application/json")
    _error(response, 400, "http.bad_request")


def test_domain_not_found():
    """A missing user answers 404 users.not_found with the searched param and scope."""
    client, _ = _client()
    error = _error(client.get("/api/v1/users/nope"), 404, "users.not_found")
    assert error["param"] == "uid"
    assert error["details"]["search_params"] == {"uid": "nope"}
    assert error["details"]["scope"] == "get"


def test_not_found_by_several_criteria():
    """A lookup by several criteria lists all of them in param and message."""
    error = NotFoundError(
        "users.not_found", search_params={"first_name": "Ana", "last_name": "Pérez"}
    ).to_dict()["error"]
    assert error["param"] == "first_name, last_name"
    assert error["message"].startswith("El(la) usuario con los parámetros de búsqueda")
    assert "first_name: Ana, last_name: Pérez" in error["message"]


def test_unknown_route_and_method():
    """Flask's own 404 and 405 answer in the same format with http.* codes."""
    client, _ = _client()
    _error(client.get("/api/v1/nope"), 404, "http.not_found")
    _error(client.delete("/api/v1/users"), 405, "http.method_not_allowed")


def test_unhandled_error_hides_details_and_logs_traceback():
    """An unexpected exception answers a generic 500 and logs its traceback."""
    client, logger = _client()
    error = _error(client.get("/boom"), 500, "internal_error")
    assert error["type"] == "api_error"
    assert "secret" not in str(error)
    assert ("log_exception", "internal_error") in logger.calls


def test_client_errors_log_as_warning():
    """Client errors are logged as warnings under their log_event key."""
    client, logger = _client()
    client.get("/api/v1/users/nope")
    assert ("log_warning", "users.get.not_found") in logger.calls


def test_every_raised_code_is_in_the_catalog():
    """Every code raised in src exists in the error dictionary.

    Catches a code typed in a raise but missing from the catalog, e.g.
    ``NotFoundError("users.not_fond", ...)``.
    """
    raised = set()
    for path in SRC_DIR.rglob("*.py"):
        raised |= set(re.findall(r'Error\(\s*"([a-z_.]+)"', path.read_text(encoding="utf-8")))
    assert raised, "no error codes found, the pattern is stale"
    assert raised <= ERROR_CATALOG.keys(), raised - ERROR_CATALOG.keys()


def test_catalog_entries_are_complete():
    """Every catalog entry has a valid type that agrees with its status."""
    for code, entry in ERROR_CATALOG.items():
        assert entry["type"] in {"invalid_request_error", "api_error"}, code
        assert (entry["type"] == "api_error") == (entry["http_status"] >= 500), code


def test_categories_take_status_and_type_from_the_catalog():
    """Error classes take status and type from the catalog entry of their code."""
    for error in [
        NotFoundError("users.not_found", search_params={"uid": "u1"}),
        ParamRequiredError("users.param_required", param_name="uid"),
        InternalError("users.internal_error"),
    ]:
        entry = ERROR_CATALOG[error.error_code]
        assert error.status_code == entry["http_status"], error.error_code
        assert error.error_type == entry["type"], error.error_code


def test_internal_error_never_exposes_the_technical_message():
    """InternalError keeps its technical message for the logs only."""
    error = InternalError("users.internal_error", message="firestore write timed out")
    assert error.message == "firestore write timed out"
    assert "firestore" not in error.to_dict()["error"]["message"]
