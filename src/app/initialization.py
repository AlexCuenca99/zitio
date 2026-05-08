"""Application initialization module."""

from src.infra.db.firestore import firestore_client
from src.interactor.interfaces.logger import LoggerInterface


class ConnectionInitializer:
    """Handles application connection initialization at startup."""

    def __init__(self, logger: LoggerInterface):
        self.logger = logger

    def initialize_all(self) -> bool:
        """Initialize all connections at application startup."""
        results = {
            "firestore": self.initialize_firestore(),
        }

        if all(results.values()):
            self.logger.log_info("✓ All connections initialized successfully")
            return True
        else:
            self.logger.log_error(f"✗ Connection initialization failed: {results}")
            return False

    def initialize_firestore(self) -> bool:
        """Initialize Firestore connection."""
        try:
            list(firestore_client.collections())
            self.logger.log_info("✓ Firestore connection OK")
            return True
        except Exception as e:
            self.logger.log_error(f"✗ Firestore connection failed: {e}")
            return False
