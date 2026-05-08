"""This module defines the Default Logger"""

# Natives
import logging
from typing import Any

# Third-parties
import google.cloud.logging
from flask import has_request_context, request

# Interfaces
from src.interactor.interfaces.logger import LoggerInterface

# Constants
from src.utils.constants import (
    ENVIRONMENT,
    LOG_LEVEL,
    LOGGING_TRACE_CONTEXT_HEADER,
    PRODUCTION_ENVIRONMENT,
    PROJECT_ID,
    SERVICE_NAME,
    SHOW_TRACEBACK,
)


class LoggerDefault(LoggerInterface):
    """LoggerDefault class."""

    def __init__(self, environment: str = PRODUCTION_ENVIRONMENT):
        self.show_traceback = SHOW_TRACEBACK
        self.project_id = PROJECT_ID
        self.service_name = SERVICE_NAME
        self.environment = ENVIRONMENT
        self.runtime_environment = environment
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(LOG_LEVEL)

        if environment == PRODUCTION_ENVIRONMENT:
            client = google.cloud.logging.Client()
            client.setup_logging()
            self.logger.info(
                "LOGGER_BOOTSTRAP_PROD",
                extra={
                    "labels": {
                        "log_type": "logger_bootstrap",
                        "service": self.service_name,
                        "environment": self.environment,
                    },
                    "logger_init_mode": "google_cloud_logging",
                    "project_id": self.project_id,
                },
            )
        else:
            logging.basicConfig(
                datefmt="%Y-%m-%d %H:%M:%S",
                format="%(asctime)-s - %(levelname)s - %(message)s",
                level=LOG_LEVEL,
            )
            self.logger.info(
                "LOGGER_BOOTSTRAP_LOCAL",
                extra={
                    "labels": {
                        "log_type": "logger_bootstrap",
                        "service": self.service_name,
                        "environment": self.environment,
                    },
                    "logger_init_mode": "basic_config",
                },
            )

    @staticmethod
    def _extract_trace_id_from_request() -> str | None:
        """Extract trace_id from X-Cloud-Trace-Context header when request context exists."""
        if not has_request_context():
            return None

        trace_header = request.headers.get(LOGGING_TRACE_CONTEXT_HEADER, "")
        if not trace_header:
            return None

        trace_id = trace_header.split("/")[0].strip()
        return trace_id or None

    def _build_extra(self, **context: Any) -> dict[str, Any]:
        reserved_keys = {"log_type", "trace_id", "exc_info"}

        labels = {
            "log_type": context.get("log_type", "general"),
            "service": self.service_name,
            "environment": self.environment,
        }

        extra: dict[str, Any] = {"labels": labels}

        trace_id = context.get("trace_id") or self._extract_trace_id_from_request()
        if trace_id and self.project_id:
            extra["trace"] = f"projects/{self.project_id}/traces/{trace_id}"

        for key, value in context.items():
            if key not in reserved_keys and value is not None:
                extra[key] = value

        return extra

    def _log(self, level, message: str, **context: Any) -> str | None:
        extra = self._build_extra(**context)
        exc_info = context.get("exc_info", False)

        # In production, emit structured payload so custom keys appear in jsonPayload.
        if self.runtime_environment == PRODUCTION_ENVIRONMENT:
            payload = {"message": message}
            for key, value in extra.items():
                if key != "labels":
                    payload[key] = value

            self.logger.log(
                level,
                payload,
                extra={"labels": extra.get("labels", {})},
                exc_info=exc_info,
            )
        else:
            self.logger.log(level, message, extra=extra, exc_info=exc_info)

        return context.get("correlation_id")

    def log_debug(self, message: str, **context: Any) -> str | None:
        return self._log(logging.DEBUG, message, **context)

    def log_info(self, message: str, **context: Any) -> str | None:
        return self._log(logging.INFO, message, **context)

    def log_warning(self, message: str, **context: Any) -> str | None:
        return self._log(logging.WARNING, message, **context)

    def log_error(self, message: str, **context: Any) -> str | None:
        return self._log(logging.ERROR, message, **context)

    def log_critical(self, message: str, **context: Any) -> str | None:
        return self._log(logging.ERROR, message, **context)

    def log_exception(self, message: str, **context: Any) -> str | None:
        context["exc_info"] = True
        return self._log(logging.ERROR, message, **context)
