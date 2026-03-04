"""Global pytest configuration and fixtures for the EC Issuer project."""

import pytest

from src.issuer_agent_adapter.hardcoded_adapter import HardcodedIssuerAgentAdapter
from src.main import create_app


@pytest.fixture(scope="session")
def app():
    """Create and configure the Flask app for testing."""
    # Use the hardcoded adapter for testing
    app = create_app(HardcodedIssuerAgentAdapter())
    app.config.update(
        {
            "TESTING": True,
        }
    )
    return app


@pytest.fixture(scope="session")
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    """Create a test runner for the Flask app."""
    return app.test_cli_runner()
