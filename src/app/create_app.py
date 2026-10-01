"""This module defines the Flask app creation for the Zitio project."""

# Natives
import json
import time

# Third-parties
from flask import Blueprint, Flask, Response, g
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

# Locals
from src.infra.loggers.logger_default import LoggerDefault
from src.interactor.errors import (
    BaseError,
    InternalError,
    ParamInvalidError,
    ParamRequiredError,
)
from src.utils.content_types import (
    APPLICATION_JSON,
    CONTENT_TYPE,
    is_multipart,
)

# Client messages for the HTTP errors Flask/werkzeug raise on their own (or via abort()).
HTTP_CLIENT_MESSAGES = {
    400: "La solicitud no es válida.",
    401: "No autenticado.",
    403: "No tienes permisos para realizar esta acción.",
    404: "El recurso solicitado no existe.",
    405: "Método no permitido para este recurso.",
    409: "La solicitud entra en conflicto con el estado actual del recurso.",
    415: "Tipo de contenido no soportado.",
    429: "Demasiadas solicitudes. Intenta más tarde.",
}


def _register_error_handlers(app: Flask, logger: LoggerDefault) -> None:
    """Register the handlers that turn every error into the BaseError.to_dict body.

    Args:
        app: Flask application to register the handlers on.
        logger: Logger the handlers report every error to.
    """

    def base_error_handler(error: BaseError) -> tuple[dict, int]:
        """Log an API error and answer with its body and status.

        Client errors (4xx) are logged as warnings; server errors (5xx) as errors with
        the traceback.

        Args:
            error: Error to report.

        Returns:
            The error body and its HTTP status code.
        """
        trace_id = logger.extract_trace_id_from_request()
        context = {
            "log_type": "app_error",
            "trace_id": trace_id,
            "error_code": error.error_code,
            "status_code": error.status_code,
            "error_message": error.message,
            "details": error.details or None,
        }
        if error.status_code >= 500:
            logger.log_exception(error.log_event, **context)
        else:
            logger.log_warning(error.log_event, **context)

        return error.to_dict(request_id=trace_id), error.status_code

    def validation_error_handler(error: ValidationError) -> tuple[dict, int]:
        """Map an unhandled Pydantic ValidationError to the standard error response.

        A missing field and a malformed one are different failures: reporting both as
        "required" sends the caller looking for a field it did send.

        Args:
            error: Validation error raised while building a model from client input.

        Returns:
            The error body and its HTTP status code, from base_error_handler.
        """
        # Only loc/type/msg: input may echo sensitive data and ctx may not serialize.
        errors = [
            {
                # An empty loc means the whole body failed (e.g. a JSON list or null).
                "param": ".".join(str(part) for part in item["loc"]) or "body",
                "type": item["type"],
                "reason": item["msg"],
            }
            for item in error.errors()
        ]
        first = errors[0]

        if first["type"] == "missing":
            return base_error_handler(
                ParamRequiredError(param_name=first["param"], scope=error.title)
            )
        return base_error_handler(
            ParamInvalidError(
                param_name=first["param"],
                reason=first["reason"],
                scope=error.title,
                errors=errors,
            )
        )

    def http_error_handler(error: HTTPException) -> tuple[dict, int]:
        """Map an HTTP error raised by Flask or werkzeug to the standard error response.

        Args:
            error: HTTP error such as a 404 for an unknown route or a 405 method.

        Returns:
            The error body with an ``http.<name>`` code and its HTTP status code.
        """
        status_code = error.code or 500
        name = (error.name or "error").lower().replace(" ", "_")
        return base_error_handler(
            BaseError(
                status_code=status_code,
                message=error.description,
                client_message=HTTP_CLIENT_MESSAGES.get(
                    status_code,
                    "Ocurrió un error interno."
                    if status_code >= 500
                    else "La solicitud no es válida.",
                ),
                error_code=f"http.{name}",
                error_type="api_error" if status_code >= 500 else "invalid_request_error",
            )
        )

    def unhandled_error_handler(error: Exception) -> tuple[dict, int]:
        """Answer any unexpected exception with a generic 500.

        The original error never reaches the client; its traceback goes to the logs.

        Args:
            error: Exception no other handler matched.

        Returns:
            The internal error body and the 500 status code.
        """
        trace_id = logger.extract_trace_id_from_request()
        logger.log_exception(
            "internal_error",
            log_type="app_error",
            trace_id=trace_id,
            error=repr(error),
        )
        internal = InternalError()
        return internal.to_dict(request_id=trace_id), 500

    app.register_error_handler(BaseError, base_error_handler)
    app.register_error_handler(ValidationError, validation_error_handler)
    app.register_error_handler(HTTPException, http_error_handler)
    app.register_error_handler(Exception, unhandled_error_handler)


def create_app(blueprints: list[Blueprint], logger: LoggerDefault) -> Flask:
    """Create and configure the Flask application.

    Args:
        blueprints: Blueprints to register.
        logger: Logger the error handlers report to.

    Returns:
        The configured application with its blueprints and error handlers.
    """
    app = Flask(__name__)
    app.config["logger"] = logger

    # Avoid flask auto-sort keys in api response (preserves ordering)
    app.json.sort_keys = False

    # Register centralized handlers
    _register_error_handlers(app, logger)

    @app.before_request
    def before_request() -> None:
        """Store the request start time to measure its execution time."""
        g.start = time.perf_counter()

    @app.after_request
    def after_request(response: Response) -> Response:
        """Append the execution time to successful responses.

        Args:
            response: Response about to be sent.

        Returns:
            The same response, with ``meta.exec_seconds`` when its status is 200.
        """
        # Append execution time and keep existing logic
        if response.status_code == 200:
            append_time_execution_after_request(response)
        return response

    # Register blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    return app


def append_time_execution_after_request(response: Response) -> Response:
    """Append the execution time to a JSON response.

    Args:
        response: Response whose JSON body gets ``meta.exec_seconds``.

    Returns:
        The same response; multipart and non-dict bodies are left untouched.
    """

    content_type = response.headers.get(CONTENT_TYPE, "")

    if not is_multipart(content_type):
        try:
            payload = response.get_json(silent=True)
        except Exception:
            payload = None

        if isinstance(payload, dict):
            total_time = time.perf_counter() - getattr(g, "start", time.perf_counter())
            meta = payload.get("meta") or {}
            meta["exec_seconds"] = total_time
            payload["meta"] = meta
            response.set_data(json.dumps(payload))
            response.headers[CONTENT_TYPE] = APPLICATION_JSON

    return response
