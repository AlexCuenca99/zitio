"""This module defines the constants for the application"""

# Natives
import os


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


PRODUCTION_ENVIRONMENT = "production"
DEVELOPMENT_ENVIRONMENT = "development"

DEV_ENVIRONMENTS = [
    PRODUCTION_ENVIRONMENT,
    DEVELOPMENT_ENVIRONMENT,
]
ENVIRONMENT = os.getenv("ENVIRONMENT", DEVELOPMENT_ENVIRONMENT)
SHOW_TRACEBACK = _env_bool("SHOW_TRACEBACK", default="false")
PROJECT_ID = os.getenv("PROJECT_ID")
SERVICE_NAME = os.getenv("SERVICE_NAME", "zitio")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOGGING_TRACE_CONTEXT_HEADER = "X-Cloud-Trace-Context"
