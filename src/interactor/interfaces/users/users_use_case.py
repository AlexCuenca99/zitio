"""Contract for the consolidated Users use case."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class UsersUseCaseInterface(ABC):
    """Single use case exposing multiple user operations."""

    @abstractmethod
    def create(self, payload: dict) -> Dict:
        ...

    @abstractmethod
    def get(self, uid: str) -> Dict:
        ...

    @abstractmethod
    def get_by_id(self, uid: str) -> Dict:
        ...

    @abstractmethod
    def list(self) -> Dict:
        ...
