"""This module defines the Firestore implementation of the users repository."""

# Third-parties
from google.api_core.exceptions import Conflict
from google.api_core.exceptions import NotFound as FirestoreNotFound
from google.cloud.firestore import Client

# Locals
from src.domain.entities.user import User
from src.interactor.errors import ConflictError, NotFoundError
from src.interactor.interfaces.users.users_repository import UsersRepositoryInterface


class UsersFirestoreRepository(UsersRepositoryInterface):
    """Users repository backed by the ``users`` Firestore collection."""

    def __init__(self, firestore_client: Client):
        """Initialize the repository.

        Args:
            firestore_client: Firestore client to read and write with.
        """
        self.firestore = firestore_client
        self.collection_name = "users"

    def create(self, user: User) -> User:
        """Persist a new user, never overwriting an existing one.

        Args:
            user: User to persist; its uid is the document id.

        Returns:
            The persisted user.

        Raises:
            ConflictError: If a user with that uid already exists ("users.already_exists").
        """
        document = self.firestore.collection(self.collection_name).document(user.uid)
        try:
            # create() fails when the document exists, unlike set(), which overwrites it.
            document.create(user.model_dump(mode="json"))
        except Conflict as error:
            raise ConflictError(
                "users.already_exists",
                message=str(error),
                search_params={"uid": user.uid},
                scope="create",
            ) from error
        return user

    def get_by_uid(self, uid: str) -> User | None:
        """Get a user by uid.

        Args:
            uid: Identifier of the user.

        Returns:
            The user, or None when it does not exist.
        """
        doc = self.firestore.collection(self.collection_name).document(uid).get()
        if not doc.exists:
            return None
        return User.model_validate(doc.to_dict())

    def update(self, user: User) -> User:
        """Replace the stored data of an existing user.

        Args:
            user: User with the new data; its uid selects the document.

        Returns:
            The updated user.

        Raises:
            NotFoundError: If no user has that uid ("users.not_found").
        """
        document = self.firestore.collection(self.collection_name).document(user.uid)
        try:
            # update() fails when the document does not exist, unlike set().
            document.update(user.model_dump(mode="json"))
        except FirestoreNotFound as error:
            raise NotFoundError(
                "users.not_found", search_params={"uid": user.uid}, scope="update"
            ) from error
        return user
