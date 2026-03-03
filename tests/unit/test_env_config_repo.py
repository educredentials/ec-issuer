"""Tests for EnvConfigRepo implementation."""

import pytest

from src.config import EnvConfigRepo


@pytest.mark.unit
class TestEnvConfigRepo:
    """Test EnvConfigRepo implementation."""

    def test_missing_env_vars(self):
        """Test that missing environment variables raise KeyError."""
        # Test with empty environment
        with pytest.raises(KeyError):
            EnvConfigRepo(env={})

    def test_valid_env_vars(self):
        """Test that valid environment variables are loaded correctly."""
        # Test with valid environment
        test_env = {"SERVER_HOST": "127.0.0.1", "SERVER_PORT": "9000"}

        config = EnvConfigRepo(env=test_env)
        assert config.server_host == "127.0.0.1"
        assert config.server_port == 9000

    def test_invalid_server_port(self):
        """Test that invalid SERVER_PORT raises ValueError."""
        # Test with invalid port value
        invalid_env = {"SERVER_HOST": "0.0.0.0", "SERVER_PORT": "not_a_number"}

        with pytest.raises(ValueError):
            EnvConfigRepo(env=invalid_env)

    def test_default_behavior_uses_os_environ(self, monkeypatch):
        """Test that EnvConfigRepo() without args uses os.environ."""
        # Set up test environment variables
        monkeypatch.setenv("SERVER_HOST", "localhost")
        monkeypatch.setenv("SERVER_PORT", "8080")

        # Create repo without arguments (should use os.environ)
        config = EnvConfigRepo()
        assert config.server_host == "localhost"
        assert config.server_port == 8080
