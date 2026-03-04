"""Unit tests for the EnvConfigRepo."""

import pytest

from src.config import EnvConfigRepo


class TestEnvConfigRepo:
    """Test the EnvConfigRepo class."""

    def test_missing_env_vars(self):
        """Test that missing environment variables raise KeyError."""
        with pytest.raises(KeyError):
            EnvConfigRepo(env={})

    def test_valid_env_vars(self):
        """Test that valid environment variables are parsed correctly."""
        env = {
            "SERVER_HOST": "localhost",
            "SERVER_PORT": "8080",
            "ISSUER_AGENT_BASE_URL": "http://issuer.example.com",
        }
        config = EnvConfigRepo(env=env)

        assert config.server_host == "localhost"
        assert config.server_port == 8080
        assert config.issuer_agent_base_url == "http://issuer.example.com"

    def test_invalid_server_port(self):
        """Test that invalid server port raises ValueError."""
        env = {
            "SERVER_HOST": "localhost",
            "SERVER_PORT": "invalid",
            "ISSUER_AGENT_BASE_URL": "http://issuer.example.com",
        }
        with pytest.raises(ValueError):
            EnvConfigRepo(env=env)

    def test_default_behavior_uses_os_environ(self, monkeypatch):
        """Test that default behavior uses os.environ."""
        monkeypatch.setenv("SERVER_HOST", "localhost")
        monkeypatch.setenv("SERVER_PORT", "8080")
        monkeypatch.setenv("ISSUER_AGENT_BASE_URL", "http://issuer.example.com")

        config = EnvConfigRepo()

        assert config.server_host == "localhost"
        assert config.server_port == 8080
        assert config.issuer_agent_base_url == "http://issuer.example.com"
