"""This module defines the contract every users repository implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.user import User


class UsersRepositoryInterface(ABC):
    """Repository contract for user persistence."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Persist a new user, never overwriting an existing one.

        Args:
            user: User to persist; its uid is the document id.

        Returns:
            The persisted user.

        Raises:
            ConflictError: If a user with that uid already exists ("users.already_exists").
        """

    @abstractmethod
    def get_by_uid(self, uid: str) -> User | None:
        """Get a user by uid.

        Args:
            uid: Identifier of the user.

        Returns:
            The user, or None when it does not exist.
        """

    @abstractmethod
    def update(self, user: User) -> User:
        """Replace the stored data of an existing user.

        Args:
            user: User with the new data; its uid selects the document.

        Returns:
            The updated user.

        Raises:
            NotFoundError: If no user has that uid ("users.not_found").
        """
