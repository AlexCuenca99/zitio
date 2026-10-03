"""This module defines the test doubles shared by the test modules."""

from src.interactor.errors import ConflictError, NotFoundError, UnauthenticatedError

VALID_TOKEN = "valid-token"
EXPIRED_TOKEN = "expired-token"
NO_EMAIL_TOKEN = "no-email-token"
AUTHENTICATED_UID = "user-1"
AUTHENTICATED_EMAIL = "user-1@zitio.com"


class InMemoryUsersRepository:
    """Users repository kept in memory that fails like the Firestore one."""

    def __init__(self):
        """Start with no users."""
        self.users = {}

    def create(self, user):
        """Store a new user.

        Args:
            user: User entity to store.

        Returns:
            The stored user.

        Raises:
            ConflictError: If the uid is already stored ("users.already_exists").
        """
        if user.uid in self.users:
            raise ConflictError(
                "users.already_exists", search_params={"uid": user.uid}, scope="create"
            )
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

    def update(self, user):
        """Replace a stored user.

        Args:
            user: User entity with the new data.

        Returns:
            The updated user.

        Raises:
            NotFoundError: If the uid is not stored ("users.not_found").
        """
        if user.uid not in self.users:
            raise NotFoundError("users.not_found", search_params={"uid": user.uid}, scope="update")
        self.users[user.uid] = user
        return user


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


def fake_verify_id_token(token: str) -> dict:
    """Stand in for Firebase token verification.

    Args:
        token: Bearer token sent by the test client.

    Returns:
        The identity of ``AUTHENTICATED_UID``: with ``AUTHENTICATED_EMAIL`` for
        ``VALID_TOKEN`` and without email for ``NO_EMAIL_TOKEN``.

    Raises:
        UnauthenticatedError: "auth.token_expired" for ``EXPIRED_TOKEN`` and
            "auth.token_invalid" for any other token.
    """
    if token == VALID_TOKEN:
        return {"uid": AUTHENTICATED_UID, "email": AUTHENTICATED_EMAIL}
    if token == NO_EMAIL_TOKEN:
        return {"uid": AUTHENTICATED_UID, "email": None}
    if token == EXPIRED_TOKEN:
        raise UnauthenticatedError("auth.token_expired")
    raise UnauthenticatedError("auth.token_invalid")
