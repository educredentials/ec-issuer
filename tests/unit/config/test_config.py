"""Test ConfigRepoPort and EnvConfigRepo."""

from unittest.mock import patch

import pytest

from src.config.config import EnvConfigRepo


def _make_env(
    server_host: str = "0.0.0.0",
    server_port: int = 8000,
    ssi_agent_url: str = "http://agent.example.com",
    awards_service_url: str = "http://awards.example.com",
    postgresql_connection_string: str = "postgresql://localhost/test",
    allowed_cors_domains: str = "http://localhost:8000,https://app.example.com",
) -> dict[str, str]:
    """Return a minimal env dict with required keys."""
    return {
        "SERVER_HOST": server_host,
        "SERVER_PORT": str(server_port),
        "SSI_AGENT_URL": ssi_agent_url,
        "AWARDS_SERVICE_URL": awards_service_url,
        "POSTGRES_CONNECTION_STRING": postgresql_connection_string,
        "ALLOWED_CORS_DOMAINS": allowed_cors_domains,
    }


class TestEnvConfigRepo:
    """Tests for EnvConfigRepo."""

    def test_missing_env_vars(self) -> None:
        """Missing required env vars raises KeyError."""
        with pytest.raises(KeyError):
            _ = EnvConfigRepo(env={})

    def test_missing_allowed_cors_domains_raises_keyerror(self) -> None:
        """Missing ALLOWED_CORS_DOMAINS raises KeyError."""
        env = _make_env()
        del env["ALLOWED_CORS_DOMAINS"]

        with pytest.raises(KeyError):
            _ = EnvConfigRepo(env=env)

    def test_valid_env_vars(self) -> None:
        """Valid env vars produce a config with correct values."""
        env = _make_env()
        config = EnvConfigRepo(env=env)

        assert config.server_host == "0.0.0.0"
        assert config.server_port == 8000
        assert config.ssi_agent_url == "http://agent.example.com"
        assert config.awards_service_url == "http://awards.example.com"
        assert config.debug is True
        assert config.postgresql_connection_string == "postgresql://localhost/test"
        assert (
            config.allowed_cors_domains
            == "http://localhost:8000,https://app.example.com"
        )
        assert config.credential_configuration_id == ""

    def test_invalid_server_port(self) -> None:
        """Invalid SERVER_PORT raises ValueError."""
        env = _make_env()
        env["SERVER_PORT"] = "not_a_port"
        with pytest.raises(ValueError):
            _ = EnvConfigRepo(env=env)

    def test_default_behavior_uses_os_environ(self) -> None:
        """EnvConfigRepo uses os.environ as the default mapping."""
        env = _make_env()
        with patch.dict("os.environ", env):
            config = EnvConfigRepo()

        assert config.server_host == "0.0.0.0"

    def test_pre_resolved_id(self) -> None:
        """Credential template id can be pre-resolved."""
        env = _make_env()
        config = EnvConfigRepo(env=env, credential_configuration_id="pre-resolved-id")

        assert config.credential_configuration_id == "pre-resolved-id"

    def test_default_credential_configuration_id_is_empty(self) -> None:
        """credential_configuration_id defaults to empty string."""
        env = _make_env()
        config = EnvConfigRepo(env=env)

        assert config.credential_configuration_id == ""

