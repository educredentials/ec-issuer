"""Pytest configuration and fixtures for integration tests."""

import pytest


@pytest.fixture
def postgresql_connection_string() -> str:
    """Provide PostgreSQL connection string for integration tests.

    The PostgreSQL service must be running before tests are executed.
    """
    return "postgresql://ecissuer:ecissuer@localhost:5432/ecissuer"
