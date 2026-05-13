"""Pytest configuration and fixtures for integration tests."""

import os
from collections.abc import Generator

import pytest

from src.metadata.postgresql_adapter import PostgreSQLMetadataRepository
from src.offers.postgresql_offers_repository_adapter import (
    PostgreSQLOffersRepositoryAdapter,
)
from src.offers.ssi_agent_offers_client_adapter import SsiAgentOffersClientAdapter

_CONNECTION_STRING = os.environ["POSTGRES_CONNECTION_STRING"]
_SSI_AGENT_URL = os.environ["SSI_AGENT_URL"]


@pytest.fixture(scope="session")
def postgresql_connection_string() -> str:
    """Provide PostgreSQL connection string for integration tests.

    The PostgreSQL service must be running before tests are executed.
    """
    return _CONNECTION_STRING


@pytest.fixture(scope="session")
def metadata_repo() -> Generator[PostgreSQLMetadataRepository, None, None]:
    """Provide a single PostgreSQLMetadataRepository for the test session.

    Initialises the database once and closes the connection on teardown.
    """
    repo = PostgreSQLMetadataRepository(_CONNECTION_STRING)
    yield repo
    repo.close_db()


@pytest.fixture(scope="session")
def offers_repo() -> Generator[PostgreSQLOffersRepositoryAdapter, None, None]:
    repo = PostgreSQLOffersRepositoryAdapter(_CONNECTION_STRING)
    yield repo
    repo.close_db()


@pytest.fixture(scope="session")
def offers_client() -> SsiAgentOffersClientAdapter:
    return SsiAgentOffersClientAdapter(ssi_agent_url=_SSI_AGENT_URL)
