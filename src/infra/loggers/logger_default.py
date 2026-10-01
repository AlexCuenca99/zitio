"""This module defines the default logger, backed by Cloud Logging in production."""

# Natives
import logging
from typing import Any

# Third-parties
import google.cloud.logging
from flask import has_request_context, request

# Locals
from configs.config import settings

# Interfaces
from src.interactor.interfaces.logger import LoggerInterface

# Constants
from src.utils.constants import LOGGING_TRACE_CONTEXT_HEADER, PRODUCTION_ENVIRONMENT


class LoggerDefault(LoggerInterface):
    """Logger that writes structured entries to Cloud Logging or the local console."""

    def __init__(self, environment: str = PRODUCTION_ENVIRONMENT):
        """Configure the logger for the runtime environment.

        Args:
            environment: Runtime environment; production sends entries to Cloud Logging,
                any other value logs to the console.
        """
        self.show_traceback = settings.show_traceback
        self.project_id = settings.project_id
        self.service_name = settings.service_name
        self.environment = settings.environment
        self.runtime_environment = environment
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(settings.log_level)

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
                level=settings.log_level,
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
    def extract_trace_id_from_request() -> str | None:
        """Extract the trace id of the current request.

        Returns:
            The trace id from the X-Cloud-Trace-Context header, or None outside a
            request or when the header is missing.
        """
        if not has_request_context():
            return None

        trace_header = request.headers.get(LOGGING_TRACE_CONTEXT_HEADER, "")
        if not trace_header:
            return None

        trace_id = trace_header.split("/")[0].strip()
        return trace_id or None

    def _build_extra(self, **context: Any) -> dict[str, Any]:
        """Build the structured fields attached to a log entry.

        Args:
            **context: Context fields of the entry; ``log_type`` and ``trace_id`` are
                turned into labels and the Cloud Trace link.

        Returns:
            The ``extra`` mapping with labels, trace link and the remaining context.
        """
        reserved_keys = {"log_type", "trace_id", "exc_info"}

        labels = {
            "log_type": context.get("log_type", "general"),
            "service": self.service_name,
            "environment": self.environment,
        }

        extra: dict[str, Any] = {"labels": labels}

        trace_id = context.get("trace_id") or self.extract_trace_id_from_request()
        if trace_id and self.project_id:
            extra["trace"] = f"projects/{self.project_id}/traces/{trace_id}"

        for key, value in context.items():
            if key not in reserved_keys and value is not None:
                extra[key] = value

        return extra

    def _log(self, level: int, message: str, **context: Any) -> str | None:
        """Emit a log entry at the given level.

        Args:
            level: Standard logging level.
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
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
        """Log a debug-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
        return self._log(logging.DEBUG, message, **context)

    def log_info(self, message: str, **context: Any) -> str | None:
        """Log an info-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
        return self._log(logging.INFO, message, **context)

    def log_warning(self, message: str, **context: Any) -> str | None:
        """Log a warning-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
        return self._log(logging.WARNING, message, **context)

    def log_error(self, message: str, **context: Any) -> str | None:
        """Log an error-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
        return self._log(logging.ERROR, message, **context)

    def log_critical(self, message: str, **context: Any) -> str | None:
        """Log a critical message, emitted at error level.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
        return self._log(logging.ERROR, message, **context)

    def log_exception(self, message: str, **context: Any) -> str | None:
        """Log an error-level message with the traceback of the exception being handled.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The ``correlation_id`` passed in the context, if any.
        """
        context["exc_info"] = True
        return self._log(logging.ERROR, message, **context)
