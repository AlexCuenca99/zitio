"""Consolidated UsersUseCase implementing the UsersUseCaseInterface."""

from __future__ import annotations

from datetime import date

from src.domain.entities.user import User
from src.interactor.errors.users.users_errors import UsersNotFoundError
from src.interactor.interfaces.logger import LoggerInterface
from src.interactor.interfaces.users.users_repository import UsersRepositoryInterface
from src.interactor.interfaces.users.users_use_case import UsersUseCaseInterface


def _age_from_birthdate(birth_date: date) -> int:
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


class UsersUseCase(UsersUseCaseInterface):
    """Single use case exposing several user operations."""

    def __init__(self, users_repository: UsersRepositoryInterface, logger: LoggerInterface):
        self.users_repository = users_repository
        self.logger = logger

    def create(self, payload: dict) -> dict:
        user = User.model_validate(payload)
        created = self.users_repository.create(user)
        self.logger.log_info("user_created", log_type="user_creation", uid=created.uid)
        return {"status": "success", "data": created.model_dump(mode="json")}

    def get(self, uid: str) -> dict:
        user = self.users_repository.get_by_uid(uid)
        if user is None:
            raise UsersNotFoundError(search_params={"uid": uid})

        return {"status": "success", "data": user.model_dump(mode="json")}

    def get_by_id(self, uid: str) -> dict:
        return self.get(uid)

    def list(self, **kwargs) -> dict:
        min_age = kwargs.get("min_age", None)
        max_age = kwargs.get("max_age", None)

        if min_age is not None:
            min_age = int(min_age)
        if max_age is not None:
            max_age = int(max_age)

        users = self.users_repository.list_all()
        filtered = []

        for user in users:
            if user.birth_date is None:
                continue

            age = _age_from_birthdate(user.birth_date)

            if min_age is not None and age < min_age:
                continue
            if max_age is not None and age > max_age:
                continue

            filtered.append(user.model_dump(mode="json"))

        return {"status": "success", "data": filtered}
