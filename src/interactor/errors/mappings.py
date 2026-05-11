"""Map known exception classes to HTTP status codes for automatic handler registration."""

from typing import Dict, Type

from src.interactor.errors.users.users_errors import (
    UsersError,
    UsersNotFoundError,
    UsersParamRequiredError,
)

# Add more entries here for other entity errors (countries, bookings, etc.)
ERROR_MAPPINGS: Dict[Type[Exception], int] = {
    UsersNotFoundError: 404,
    UsersParamRequiredError: 400,
    UsersError: 400,
}
