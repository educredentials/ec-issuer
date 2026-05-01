"""Unit tests for the EnvConfigRepo."""

import pytest

from src.config.config import EnvConfigRepo


class TestEnvConfigRepo:
    """Test the EnvConfigRepo class."""

    def test_missing_env_vars(self):
        """Test that missing environment variables raise KeyError."""
        with pytest.raises(KeyError):
            _ = EnvConfigRepo(env={})

    def test_valid_env_vars(self):
        """Test that valid environment variables are parsed correctly."""
        env = {
            "SERVER_HOST": "localhost",
            "SERVER_PORT": "8080",
            "ISSUER_AGENT_BASE_URL": "http://issuer-agent.example.com",
            "PUBLIC_URL": "https://issuer.example.com",
            "POSTGRES_CONNECTION_STRING": "postgresql://test:test@localhost:5432/test",
        }
        config = EnvConfigRepo(env=env)

        assert config.server_host == "localhost"
        assert config.server_port == 8080
        assert config.issuer_agent_base_url == "http://issuer-agent.example.com"
        assert config.public_url == "https://issuer.example.com"
        assert config.postgresql_connection_string == (
            "postgresql://test:test@localhost:5432/test"
        )

    def test_invalid_server_port(self):
        """Test that invalid server port raises ValueError."""
        env = {
            "SERVER_HOST": "localhost",
            "SERVER_PORT": "invalid",
            "ISSUER_AGENT_BASE_URL": "http://issuer-agent.example.com",
            "PUBLIC_URL": "https://issuer.example.com",
            "POSTGRES_CONNECTION_STRING": (
                "postgresql://test:test@localhost:5432/test"
            ),
        }
        with pytest.raises(ValueError):
            _ = EnvConfigRepo(env=env)

    def test_default_behavior_uses_os_environ(self, monkeypatch: pytest.MonkeyPatch):
        """Test that default behavior uses os.environ."""
        monkeypatch.setenv("SERVER_HOST", "localhost")
        monkeypatch.setenv("SERVER_PORT", "8080")
        monkeypatch.setenv("ISSUER_AGENT_BASE_URL", "http://issuer-agent.example.com")
        monkeypatch.setenv("PUBLIC_URL", "https://issuer.example.com")
        monkeypatch.setenv(
            "POSTGRES_CONNECTION_STRING",
            "postgresql://test:test@localhost:5432/test",
        )

        config = EnvConfigRepo()

        assert config.server_host == "localhost"
        assert config.server_port == 8080
        assert config.issuer_agent_base_url == "http://issuer-agent.example.com"
        assert config.public_url == "https://issuer.example.com"
        assert config.postgresql_connection_string == (
            "postgresql://test:test@localhost:5432/test"
        )
