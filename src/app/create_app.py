"""This module defines the Flask app creation for the Zitio project."""

# Natives
import json
import time
from typing import Dict, Tuple, Union

# Third-parties
from flask import Blueprint, Flask, Response, g, jsonify, request
from werkzeug.exceptions import HTTPException

# Locals
from src.infra.loggers.logger_default import LoggerDefault
from src.interactor.errors.base_errors import BaseError

# Error mappings
from src.interactor.errors.mappings import ERROR_MAPPINGS
from src.utils.content_types import (
    APPLICATION_JSON,
    CONTENT_TYPE,
    is_multipart,
)

# If you use an ApiResponseUseCase-like functionality, import it here (optional)
# from src.usecases.api_response_usecase import ApiResponseUseCase


def format_error_response(
    error: Exception,
    error_code: int,
    logger: LoggerDefault,
    is_known_exception: bool = True,
) -> Tuple[Dict[str, Union[str, int, Dict]], int]:
    """
    Format an error into a standard JSON response.

    Returns (response_dict, http_status)
    """
    # Decide what to log
    error_to_log = error.our_error if hasattr(error, "our_error") else str(error)

    # Log as info for known errors; unexpected errors as exception
    if is_known_exception:
        try:
            track_code = logger.log_info(f"{error_code} - Handled Error: {error_to_log}")
        except Exception:
            track_code = None
    else:
        try:
            track_code = logger.log_exception(f"{error_code} - Unhandled Error: {error_to_log}")
        except Exception:
            track_code = None

    # Build error object
    err_obj = {
        "type": error.__class__.__name__,
        "code": getattr(error, "error_code", None),
        "title": getattr(error, "message", None) or str(error),
        "detail": getattr(error, "details", None)
        or (
            getattr(error, "fields_with_erros", None)
            if hasattr(error, "fields_with_erros")
            else str(error)
        ),
        "trace_code": track_code,
        "gcp_issue_link": None,  # keep placeholder if you want to add link logic
    }

    # remove None values
    err_obj = {k: v for k, v in err_obj.items() if v is not None}

    response = {
        "status": "fail",
        "status_code": error_code,
        "meta": {},
        "message": str(error),
        "errors": [err_obj],
    }

    return response, error_code


def _register_error_handlers(app: Flask, logger: LoggerDefault) -> None:
    """
    Register exception handlers for Flask app using ERROR_MAPPINGS.

    Each mapping: exception class -> HTTP status code
    """

    def create_error_handler(status_code: int):
        def handle_error(error):
            return format_error_response(
                error=error, error_code=status_code, logger=logger, is_known_exception=True
            )

        return handle_error

    # Register handlers for known exception classes
    for exc_cls, status_code in ERROR_MAPPINGS.items():
        app.register_error_handler(exc_cls, create_error_handler(status_code))

    # HTTPException (werkzeug) handler
    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        try:
            logger.log_exception(str(error.__class__.__name__))
            logger.log_exception(str(error.description))
        except Exception as log_error:
            app.logger.debug("Failed to log HTTPException: %s", log_error)

        response = {"error": error.__class__.__name__, "message": error.description}
        return response, error.code

    # Generic exception handler
    @app.errorhandler(Exception)
    def handle_general_exception(error):
        # If it's our BaseError (or subclass), prefer its status_code and to_dict
        if isinstance(error, BaseError):
            # Centralize logging via logger
            try:
                logger.log_warning(
                    "APP_ERROR",
                    log_type="app_error",
                    error_code=getattr(error, "error_code", None),
                    status_code=getattr(error, "status_code", None),
                    message=str(error),
                )
            except Exception as log_error:
                app.logger.debug("Failed to log BaseError: %s", log_error)

            request_id = request.headers.get("X-Request-Id")
            return jsonify(error.to_dict(request_id=request_id)), error.status_code

        # Otherwise, treat as unexpected
        return format_error_response(error, 500, logger, is_known_exception=False)


def create_app(blueprints: list[Blueprint], logger: LoggerDefault) -> Flask:
    """
    Create and configure the Flask application, register blueprints and error handlers.
    """
    app = Flask(__name__)
    app.config["logger"] = logger

    # Avoid flask auto-sort keys in api response (preserves ordering)
    app.json.sort_keys = False

    # Register centralized handlers
    _register_error_handlers(app, logger)

    @app.before_request
    def before_request():
        g.start = time.perf_counter()

    @app.after_request
    def after_request(response: Response):
        # Append execution time and keep existing logic
        if response.status_code == 200:
            append_time_execution_after_request(response)
        return response

    # Register blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    return app


def append_time_execution_after_request(response: Response):
    """Append the execution time to the response after each request."""

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
