"""Tests for configuration management."""

import os
import pytest

from src.config import Config


@pytest.mark.unit
class TestConfig:
    """Test configuration loading from environment variables."""

    def test_default_config(self):
        """Test that default configuration values are correct."""
        # Clear environment variables to test defaults
        os.environ.pop("SERVER_HOST", None)
        os.environ.pop("SERVER_PORT", None)

        config = Config.from_env()
        assert config.server_host == "0.0.0.0"
        assert config.server_port == 8000

    def test_custom_config(self):
        """Test that custom environment variables are loaded correctly."""
        os.environ["SERVER_HOST"] = "127.0.0.1"
        os.environ["SERVER_PORT"] = "9000"

        config = Config.from_env()
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 9000

        # Clean up
        os.environ.pop("SERVER_HOST", None)
        os.environ.pop("SERVER_PORT", None)

    def test_partial_custom_config(self):
        """Test that partial custom configuration works."""
        os.environ["SERVER_HOST"] = "localhost"
        os.environ.pop("SERVER_PORT", None)

        config = Config.from_env()
        assert config.server_host == "localhost"
        assert config.server_port == 8000  # Should use default

        # Clean up
        os.environ.pop("SERVER_HOST", None)
