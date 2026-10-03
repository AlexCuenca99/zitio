"""This module defines the shared pytest fixtures, including the Firestore emulator client."""

import os

import pytest

TEST_PROJECT_ID = "zitio-test"


def pytest_configure(config: pytest.Config) -> None:
    """Set the test environment before any module builds the settings.

    Args:
        config: Pytest configuration, unused.
    """
    os.environ.setdefault("PROJECT_ID", TEST_PROJECT_ID)


def _clear_collections(client) -> None:
    """Delete every collection and its documents.

    Args:
        client: Firestore client connected to the emulator.
    """
    for collection in client.collections():
        client.recursive_delete(collection)


@pytest.fixture
def firestore_client():
    """Provide a Firestore client on the emulator, empty before and after each test.

    The test is skipped when no emulator is configured, so the cleanup can never reach
    a real Firestore database.

    Yields:
        The process-wide Firestore client, connected to the emulator.
    """
    # Imported here so pytest_configure sets the environment before settings are built.
    from configs.config import settings
    from src.infra.db.firestore import get_firestore_client

    if not settings.firestore.emulator_host:
        pytest.skip("FIRESTORE_EMULATOR_HOST is not set; start the emulator to run this test.")

    client = get_firestore_client()
    _clear_collections(client)
    yield client
    _clear_collections(client)
