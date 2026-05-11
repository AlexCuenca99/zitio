"""Contract for User repositories."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.user import User


class UsersRepositoryInterface(ABC):
    """Repository contract for user persistence."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Persist a user and return the persisted entity."""
        ...

    @abstractmethod
    def get_by_uid(self, uid: str) -> Optional[User]:
        """Return a user by uid or None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> List[User]:
        """Return all users."""
        ...
