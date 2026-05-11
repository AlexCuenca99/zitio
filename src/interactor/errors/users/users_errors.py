"""This module defines the error classes for users."""

# Natives
from typing import Any

# Locals
from src.interactor.errors.base_errors import (
    BaseError,
    BaseItemNotFoundError,
    BaseParamRequiredError,
)
from src.interactor.errors.users.users_catalog import ERROR_CATALOG


class UsersError(BaseError):
    """
    Base class for Users errors.
    """

    ERROR_CODE = "users.internal_error"

    def __init__(self, message: str | None = None, status_code: int | None = None):
        defaults = ERROR_CATALOG.get(self.ERROR_CODE, {})
        self.entity_name = "Usuarios"
        self.error_code = self.ERROR_CODE
        self.error_type = defaults.get("type")
        self.message = message or defaults.get(
            "message", f"Error en el servicio de {self.entity_name}."
        )

        super().__init__(
            status_code=status_code or defaults.get("http_status", 400),
            message=self.message,
            entity_name=self.entity_name,
            error_code=self.error_code,
            error_type=self.error_type,
        )


class UsersNotFoundError(UsersError, BaseItemNotFoundError):
    """
    Raised when a user is not found.
    """

    ERROR_CODE = "users.not_found"

    def __init__(
        self,
        entity_name: str | None = None,
        search_params: dict[str, Any] | None = None,
        possibly_unavailable: bool = False,
        possibly_hidden: bool = False,
        status_code: int | None = None,
    ):
        defaults = ERROR_CATALOG.get(self.ERROR_CODE, {})
        self.entity_name = entity_name or "Usuarios"
        self.error_code = self.ERROR_CODE
        self.error_type = defaults.get("type")

        BaseItemNotFoundError.__init__(
            self,
            status_code=status_code or defaults.get("http_status", 404),
            search_params=search_params,
            possibly_unavailable=possibly_unavailable,
            possibly_hidden=possibly_hidden,
            entity_name=self.entity_name,
            error_code=self.error_code,
            error_type=self.error_type,
            details={"reason": "not_found"},
        )


class UsersParamRequiredError(UsersError, BaseParamRequiredError):
    """
    Raised when a required user parameter is missing.
    """

    ERROR_CODE = "users.uid_required"

    def __init__(
        self,
        param_name: str | None = None,
        entity_name: str | None = None,
        status_code: int | None = None,
    ):
        defaults = ERROR_CATALOG.get(self.ERROR_CODE, {})
        self.entity_name = entity_name or "Usuarios"
        self.error_code = self.ERROR_CODE
        self.error_type = defaults.get("type")

        BaseParamRequiredError.__init__(
            self,
            status_code=status_code or defaults.get("http_status", 400),
            param_name=param_name,
            entity_name=self.entity_name,
            error_code=self.error_code,
            error_type=self.error_type,
            details={"param": param_name},
        )
