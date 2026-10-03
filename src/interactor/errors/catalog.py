"""This module defines the API error dictionary: every error code the API can return."""

from src.interactor.errors.auth.auth_catalog import ERROR_CATALOG as AUTH_CATALOG
from src.interactor.errors.users.users_catalog import ERROR_CATALOG as USERS_CATALOG

COMMON_CATALOG = {
    "internal_error": {
        "type": "api_error",
        "http_status": 500,
        "message": "Unexpected internal error.",
        "client_message": "Ocurrió un error interno.",
    },
    "request.param_required": {
        "type": "invalid_request_error",
        "http_status": 400,
    },
    "request.param_invalid": {
        "type": "invalid_request_error",
        "http_status": 400,
    },
    "resource.not_found": {
        "type": "invalid_request_error",
        "http_status": 404,
    },
}

ERROR_CATALOG = {
    **COMMON_CATALOG,
    **AUTH_CATALOG,
    **USERS_CATALOG,
}
