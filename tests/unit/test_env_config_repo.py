"""Unit tests for the EnvConfigRepo."""

import pytest

from src.config.config import EnvConfigRepo


class TestEnvConfigRepo:
    """Test the EnvConfigRepo class."""

    def test_missing_env_vars(self):
        """Test that missing environment variables raise KeyError."""
        with pytest.raises(KeyError):
            _ = EnvConfigRepo(
                env={
                    "SERVER_HOST": "localhost",
                    "SERVER_PORT": "8080",
                }
            )

    def test_valid_env_vars(self):
        """Test that valid environment variables are parsed correctly."""
        env = {
            "SERVER_HOST": "localhost",
            "SERVER_PORT": "8080",
            "SSI_AGENT_URL": "http://ssi-agent.example.com",
            "SSI_AGENT_NONCE_ENDPOINT": "http://ssi-agent.example.com/openid4vci/nonce",
            "SSI_AGENT_CREDENTIAL_ENDPOINT": "http://ssi-agent.example.com/openid4vci/credential",
            "PUBLIC_URL": "https://issuer.example.com",
            "POSTGRES_CONNECTION_STRING": "postgresql://test:test@localhost:5432/test",
        }
        config = EnvConfigRepo(env=env)

        assert config.server_host == "localhost"
        assert config.server_port == 8080
        assert config.ssi_agent_url == "http://ssi-agent.example.com"
        assert (
            config.ssi_agent_nonce_endpoint
            == "http://ssi-agent.example.com/openid4vci/nonce"
        )
        assert (
            config.ssi_agent_credential_endpoint
            == "http://ssi-agent.example.com/openid4vci/credential"
        )
        assert config.public_url == "https://issuer.example.com"
        assert config.postgresql_connection_string == (
            "postgresql://test:test@localhost:5432/test"
        )

    def test_invalid_server_port(self):
        """Test that invalid server port raises ValueError."""
        env = {
            "SERVER_HOST": "localhost",
            "SERVER_PORT": "invalid",
            "SSI_AGENT_URL": "http://ssi-agent.example.com",
            "SSI_AGENT_NONCE_ENDPOINT": "http://ssi-agent.example.com/openid4vci/nonce",
            "SSI_AGENT_CREDENTIAL_ENDPOINT": "http://ssi-agent.example.com/openid4vci/credential",
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
        monkeypatch.setenv("SSI_AGENT_URL", "http://ssi-agent.example.com")
        monkeypatch.setenv(
            "SSI_AGENT_NONCE_ENDPOINT", "http://ssi-agent.example.com/openid4vci/nonce"
        )
        monkeypatch.setenv(
            "SSI_AGENT_CREDENTIAL_ENDPOINT",
            "http://ssi-agent.example.com/openid4vci/credential",
        )
        monkeypatch.setenv("PUBLIC_URL", "https://issuer.example.com")
        monkeypatch.setenv(
            "POSTGRES_CONNECTION_STRING",
            "postgresql://test:test@localhost:5432/test",
        )

        config = EnvConfigRepo()

        assert config.server_host == "localhost"
        assert config.server_port == 8080
        assert config.ssi_agent_url == "http://ssi-agent.example.com"
        assert (
            config.ssi_agent_nonce_endpoint
            == "http://ssi-agent.example.com/openid4vci/nonce"
        )
        assert (
            config.ssi_agent_credential_endpoint
            == "http://ssi-agent.example.com/openid4vci/credential"
        )
        assert config.public_url == "https://issuer.example.com"
        assert config.postgresql_connection_string == (
            "postgresql://test:test@localhost:5432/test"
        )
