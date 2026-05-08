"""Configuration management using Ports/Adapters architecture."""

from collections.abc import Mapping
from os import environ

from src.config.config_port import ConfigRepoPort


class EnvConfigRepo(ConfigRepoPort):
    """Adapter: Configuration repository using environment variables."""

    server_host: str
    server_port: int
    ssi_agent_url: str
    ssi_agent_nonce_endpoint: str
    ssi_agent_credential_endpoint: str
    public_url: str
    debug: bool
    postgresql_connection_string: str

    def __init__(self, env: Mapping[str, str] = environ):
        """Initialize with optional environment mapping.

        Args:
            env: Environment variable mapping. Defaults to os.environ.
        """
        self.server_host = env["SERVER_HOST"]
        self.server_port = int(env["SERVER_PORT"])
        self.ssi_agent_url = env["SSI_AGENT_URL"]
        self.ssi_agent_nonce_endpoint = env["SSI_AGENT_NONCE_ENDPOINT"]
        self.ssi_agent_credential_endpoint = env["SSI_AGENT_CREDENTIAL_ENDPOINT"]
        self.public_url = env["PUBLIC_URL"]
        self.debug = False
        self.postgresql_connection_string = env["POSTGRES_CONNECTION_STRING"]
