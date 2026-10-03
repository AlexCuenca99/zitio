"""This module defines the users use case: create, get and update the caller's profile."""

from __future__ import annotations

from datetime import datetime, timezone

from src.domain.entities.user import User, UserRole
from src.interactor.errors import NotFoundError, ParamRequiredError
from src.interactor.interfaces.logger import LoggerInterface
from src.interactor.interfaces.users.users_repository import UsersRepositoryInterface
from src.interactor.use_cases.users.users_dtos import UserProfileCreate, UserProfileUpdate


class UsersUseCase:
    """Profile operations of the authenticated user, identified by the token's uid."""

    def __init__(self, users_repository: UsersRepositoryInterface, logger: LoggerInterface):
        """Initialize the use case with its dependencies.

        Args:
            users_repository: Persistence for users.
            logger: Logger for business events.
        """
        self.users_repository = users_repository
        self.logger = logger

    def create_profile(self, uid: str, email: str | None, payload: dict) -> dict:
        """Create the profile of the authenticated user as a driver.

        Args:
            uid: uid from the verified token.
            email: Email from the verified token.
            payload: Profile fields sent by the client.

        Returns:
            The success body with the created profile.

        Raises:
            ParamRequiredError: If the account has no email ("users.param_required").
            pydantic.ValidationError: If the payload has unknown or invalid fields.
            ConflictError: If the profile already exists ("users.already_exists").
        """
        if not email:
            raise ParamRequiredError("users.param_required", param_name="email", scope="create")

        fields = UserProfileCreate.model_validate(payload).model_dump(exclude_unset=True)
        user = User(uid=uid, email=email, role=UserRole.DRIVER, **fields)
        created = self.users_repository.create(user)
        self.logger.log_info("user_created", log_type="user_creation", uid=created.uid)
        return {"status": "success", "data": created.model_dump(mode="json")}

    def get_profile(self, uid: str) -> dict:
        """Get the profile of the authenticated user.

        Args:
            uid: uid from the verified token.

        Returns:
            The success body with the profile.

        Raises:
            NotFoundError: If the profile was not created yet ("users.not_found").
        """
        return {"status": "success", "data": self._get(uid, scope="get").model_dump(mode="json")}

    def update_profile(self, uid: str, payload: dict) -> dict:
        """Update the editable fields of the authenticated user's profile.

        Args:
            uid: uid from the verified token.
            payload: Fields to change: display_name, phone and/or vehicle_plate.

        Returns:
            The success body with the updated profile.

        Raises:
            pydantic.ValidationError: If the payload has unknown or invalid fields.
            NotFoundError: If the profile was not created yet ("users.not_found").
        """
        changes = UserProfileUpdate.model_validate(payload).model_dump(exclude_unset=True)
        current = self._get(uid, scope="update")

        # Re-validate the merged data so the entity's rules (e.g. plate uppercase) apply.
        updated = User.model_validate(
            {**current.model_dump(), **changes, "updated_at": datetime.now(timezone.utc)}
        )
        self.users_repository.update(updated)
        self.logger.log_info(
            "user_updated", log_type="user_update", uid=uid, fields=sorted(changes)
        )
        return {"status": "success", "data": updated.model_dump(mode="json")}

    def _get(self, uid: str, scope: str) -> User:
        """Load a profile or fail with the users catalog code.

        Args:
            uid: Identifier of the user.
            scope: Operation that needs the profile, for the error's log key.

        Returns:
            The stored user.

        Raises:
            NotFoundError: If no user has that uid ("users.not_found").
        """
        user = self.users_repository.get_by_uid(uid)
        if user is None:
            raise NotFoundError("users.not_found", search_params={"uid": uid}, scope=scope)
        return user
