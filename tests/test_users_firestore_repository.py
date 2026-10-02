"""This module defines the integration checks of the users repository against the emulator."""

from src.domain.entities.user import User
from src.infra.db.firestore.repositories import UsersFirestoreRepository


def _user(uid: str) -> User:
    """Build a valid user.

    Args:
        uid: Identifier of the user.

    Returns:
        A driver user with the given uid.
    """
    return User(uid=uid, display_name=f"User {uid}", email=f"{uid}@zitio.com", role="driver")


def test_create_then_get_by_uid(firestore_client):
    """A created user is read back with the same data."""
    repository = UsersFirestoreRepository(firestore_client=firestore_client)
    created = repository.create(_user("u1"))

    assert repository.get_by_uid("u1") == created


def test_get_missing_user_returns_none(firestore_client):
    """Reading a uid that does not exist returns None."""
    repository = UsersFirestoreRepository(firestore_client=firestore_client)

    assert repository.get_by_uid("missing") is None


def test_list_all_returns_every_user(firestore_client):
    """Listing returns every stored user, and only those."""
    repository = UsersFirestoreRepository(firestore_client=firestore_client)
    for uid in ("u1", "u2"):
        repository.create(_user(uid))

    assert sorted(user.uid for user in repository.list_all()) == ["u1", "u2"]
