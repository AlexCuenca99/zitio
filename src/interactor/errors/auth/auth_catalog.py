"""This module defines the authentication errors catalog."""

ERROR_CATALOG = {
    "auth.token_missing": {
        "type": "invalid_request_error",
        "http_status": 401,
        "message": "Missing or malformed Authorization header.",
        "client_message": "Falta el token de autenticación.",
    },
    "auth.token_invalid": {
        "type": "invalid_request_error",
        "http_status": 401,
        "message": "Invalid ID token.",
        "client_message": "El token de autenticación no es válido.",
    },
    "auth.token_expired": {
        "type": "invalid_request_error",
        "http_status": 401,
        "message": "Expired ID token.",
        "client_message": "El token de autenticación expiró.",
    },
    # The token could not be checked (e.g. Google certificates unreachable): our fault.
    "auth.internal_error": {
        "type": "api_error",
        "http_status": 500,
        "message": "Could not verify the ID token.",
        "client_message": "No se pudo verificar la autenticación.",
    },
}
