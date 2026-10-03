"""This module defines the test doubles shared by the test modules."""

from src.interactor.errors import UnauthenticatedError

VALID_TOKEN = "valid-token"
EXPIRED_TOKEN = "expired-token"
AUTHENTICATED_UID = "user-1"


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


def fake_verify_id_token(token: str) -> str:
    """Stand in for Firebase token verification.

    Args:
        token: Bearer token sent by the test client.

    Returns:
        ``AUTHENTICATED_UID`` for ``VALID_TOKEN``.

    Raises:
        UnauthenticatedError: "auth.token_expired" for ``EXPIRED_TOKEN`` and
            "auth.token_invalid" for any other token.
    """
    if token == VALID_TOKEN:
        return AUTHENTICATED_UID
    if token == EXPIRED_TOKEN:
        raise UnauthenticatedError("auth.token_expired")
    raise UnauthenticatedError("auth.token_invalid")
