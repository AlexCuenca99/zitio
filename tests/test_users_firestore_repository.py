"""This module defines the integration checks of the users repository against the emulator."""

import pytest

from src.domain.entities.user import User
from src.infra.db.firestore.repositories import UsersFirestoreRepository
from src.interactor.errors import ConflictError, NotFoundError


def _user(uid: str, **fields) -> User:
    """Build a valid user.

    Args:
        uid: Identifier of the user.
        **fields: Fields that override the defaults.

    Returns:
        A driver user with the given uid.
    """
    defaults = {"display_name": f"User {uid}", "email": f"{uid}@zitio.com", "role": "driver"}
    return User(uid=uid, **{**defaults, **fields})


def test_create_then_get_by_uid(firestore_client):
    """A created user is read back with the same data.

    Args:
        firestore_client: Firestore client on the emulator, empty for this test.
    """
    repository = UsersFirestoreRepository(firestore_client=firestore_client)
    created = repository.create(_user("u1"))

    assert repository.get_by_uid("u1") == created


def test_get_missing_user_returns_none(firestore_client):
    """Reading a uid that does not exist returns None.

    Args:
        firestore_client: Firestore client on the emulator, empty for this test.
    """
    repository = UsersFirestoreRepository(firestore_client=firestore_client)

    assert repository.get_by_uid("missing") is None


def test_create_never_overwrites(firestore_client):
    """Creating an existing uid raises users.already_exists and keeps the stored data.

    Args:
        firestore_client: Firestore client on the emulator, empty for this test.
    """
    repository = UsersFirestoreRepository(firestore_client=firestore_client)
    original = repository.create(_user("u1"))

    with pytest.raises(ConflictError) as raised:
        repository.create(_user("u1", display_name="Impostor"))

    assert raised.value.error_code == "users.already_exists"
    assert repository.get_by_uid("u1") == original


def test_update_persists_the_new_data(firestore_client):
    """Updating a stored user replaces its data.

    Args:
        firestore_client: Firestore client on the emulator, empty for this test.
    """
    repository = UsersFirestoreRepository(firestore_client=firestore_client)
    repository.create(_user("u1"))

    updated = repository.update(_user("u1", display_name="Ana", vehicle_plate="ABC-1234"))

    assert repository.get_by_uid("u1") == updated


def test_update_missing_user_is_not_found(firestore_client):
    """Updating a uid that does not exist raises users.not_found instead of creating it.

    Args:
        firestore_client: Firestore client on the emulator, empty for this test.
    """
    repository = UsersFirestoreRepository(firestore_client=firestore_client)

    with pytest.raises(NotFoundError) as raised:
        repository.update(_user("ghost"))

    assert raised.value.error_code == "users.not_found"
    assert repository.get_by_uid("ghost") is None
