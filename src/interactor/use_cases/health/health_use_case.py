"""This module defines the health use case."""


class HealthUseCase:
    def __init__(self, logger, firestore_client):
        self.logger = logger
        self.firestore_client = firestore_client

    def execute(self):
        firestore_ok = False

        try:
            list(self.firestore_client.collections())
            firestore_ok = True
        except Exception as exc:
            self.logger.log_error(f"Firestore health failed: {exc}")

        status = "ok" if firestore_ok else "error"

        return {
            "status": status,
            "services": {
                "firestore": firestore_ok,
            },
        }
