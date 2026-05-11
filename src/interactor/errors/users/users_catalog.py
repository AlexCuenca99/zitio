"""This module define the central users error catalog."""

ERROR_CATALOG = {
    "users.uid_required": {
        "type": "invalid_request_error",
        "http_status": 400,
        "message": "El parámetro 'uid' es requerido.",
    },
    "users.not_found": {
        "type": "invalid_request_error",
        "http_status": 404,
        "message": "Usuario no encontrado.",
    },
    "users.email_invalid": {
        "type": "invalid_request_error",
        "http_status": 400,
        "message": "El email no tiene formato válido.",
    },
    "users.internal_error": {
        "type": "api_error",
        "http_status": 500,
        "message": "Ocurrió un error interno.",
    },
}
