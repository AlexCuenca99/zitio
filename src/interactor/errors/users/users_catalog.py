"""This module defines the central users errors catalog."""

ERROR_CATALOG = {
    "users.internal_error": {
        "type": "api_error",
        "http_status": 500,
        "message": "An internal error occurred processing the user.",
        "client_message": "Ocurrió un error interno al procesar el usuario.",
    },
    # No message here: NotFoundError builds it from entity_name and the search params.
    "users.not_found": {
        "type": "invalid_request_error",
        "http_status": 404,
        "entity_name": "usuario",
    },
    # No message here: ParamRequiredError builds it from the missing param name.
    "users.param_required": {
        "type": "invalid_request_error",
        "http_status": 400,
        "entity_name": "usuario",
    },
}
