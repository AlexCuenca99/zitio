"""This module defines the application factory"""

# Natives
import json
import time

# Third-parties
from flask import Blueprint, Flask, Response, g

# Infra
# Locals
# Frameworks
from src.interactor.interfaces.logger import LoggerInterface

# Utils
from src.utils.content_types import (
    APPLICATION_JSON,
    CONTENT_TYPE,
    is_multipart,
)


def create_app(blueprints: list[Blueprint], logger: LoggerInterface) -> Flask:
    app = Flask(__name__)
    app.config["logger"] = logger

    @app.before_request
    def before_request():
        """
        This function is executed before each request is processed.
        """
        g.start = time.perf_counter()

    @app.after_request
    def after_request(response: Response) -> Response:
        if response.status_code == 200:
            append_time_execution_after_request(response)

        return response

    for item in blueprints:
        app.register_blueprint(item)

    return app


def append_time_execution_after_request(response: Response):
    """Append the execution time to the response after each request. It is only for non-Meli requests.

    Args:
        response (Response): The response object.

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
