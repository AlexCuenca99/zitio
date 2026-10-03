"""This module defines the public API of the errors package."""

from .base_errors import (
    BaseError,
    ConflictError,
    InternalError,
    NotFoundError,
    ParamInvalidError,
    ParamRequiredError,
    UnauthenticatedError,
)
from .catalog import ERROR_CATALOG

__all__ = [
    "ERROR_CATALOG",
    "BaseError",
    "ConflictError",
    "InternalError",
    "NotFoundError",
    "ParamInvalidError",
    "ParamRequiredError",
    "UnauthenticatedError",
]
