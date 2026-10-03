"""This module defines the users use case: create, get and list users."""

from __future__ import annotations

from src.domain.entities.user import User
from src.interactor.errors import NotFoundError
from src.interactor.interfaces.logger import LoggerInterface
from src.interactor.interfaces.users.users_repository import UsersRepositoryInterface


class UsersUseCase:
    """Single use case exposing several user operations."""

    def __init__(self, users_repository: UsersRepositoryInterface, logger: LoggerInterface):
        """Initialize the use case with its dependencies.

        Args:
            users_repository: Persistence for users.
            logger: Logger for business events.
        """
        self.users_repository = users_repository
        self.logger = logger

    def create(self, payload: dict) -> dict:
        """Validate and persist a new user.

        Args:
            payload: User fields sent by the client.

        Returns:
            The success body with the created user.

        Raises:
            pydantic.ValidationError: If the payload does not form a valid user.
        """
        user = User.model_validate(payload)
        created = self.users_repository.create(user)
        self.logger.log_info("user_created", log_type="user_creation", uid=created.uid)
        return {"status": "success", "data": created.model_dump(mode="json")}

    def get(self, uid: str) -> dict:
        """Get a user by uid.

        Args:
            uid: Identifier of the user.

        Returns:
            The success body with the user.

        Raises:
            NotFoundError: If no user has that uid ("users.not_found").
        """
        user = self.users_repository.get_by_uid(uid)
        if user is None:
            raise NotFoundError("users.not_found", search_params={"uid": uid}, scope="get")

        return {"status": "success", "data": user.model_dump(mode="json")}

    def list(self) -> dict:
        """List every user.

        Returns:
            The success body with all users.
        """
        users = self.users_repository.list_all()
        return {"status": "success", "data": [user.model_dump(mode="json") for user in users]}
