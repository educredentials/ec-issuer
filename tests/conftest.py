"""Global pytest configuration and fixtures for the EC Issuer project."""

import pytest

from src.main import create_app


@pytest.fixture(scope="session")
def app():
    """Create and configure the Flask app for testing."""
    app = create_app()
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
