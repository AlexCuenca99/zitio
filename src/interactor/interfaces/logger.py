"""This module defines the default Logger Interface"""

# Natives
from abc import ABC, abstractmethod
from typing import Any


class LoggerInterface(ABC):
    """Define the contract for application logging adapters.

    Implementations should support structured logging by accepting arbitrary
    keyword context that can be attached to each log entry.
    """

    @abstractmethod
    def log_debug(
        self,
        message: str,
        **context: Any,
    ) -> str | None:
        """Log a debug-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The emitted log message, or ``None`` if nothing was emitted.
        """
        ...

    @abstractmethod
    def log_info(
        self,
        message: str,
        **context: Any,
    ) -> str | None:
        """Log an info-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The emitted log message, or ``None`` if nothing was emitted.
        """
        ...

    @abstractmethod
    def log_warning(
        self,
        message: str,
        **context: Any,
    ) -> str | None:
        """Log a warning-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The emitted log message, or ``None`` if nothing was emitted.
        """
        ...

    @abstractmethod
    def log_error(
        self,
        message: str,
        **context: Any,
    ) -> str | None:
        """Log an error-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The emitted log message, or ``None`` if nothing was emitted.
        """
        ...

    @abstractmethod
    def log_critical(
        self,
        message: str,
        **context: Any,
    ) -> str | None:
        """Log a critical-level message.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The emitted log message, or ``None`` if nothing was emitted.
        """
        ...

    @abstractmethod
    def log_exception(
        self,
        message: str,
        **context: Any,
    ) -> str | None:
        """Log an exception with traceback context when available.

        Args:
            message: Message to log.
            **context: Extra structured context fields for the log record.

        Returns:
            The emitted log message, or ``None`` if nothing was emitted.
        """
        ...
