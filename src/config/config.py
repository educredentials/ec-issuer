"""Configuration management using Ports/Adapters architecture."""

from collections.abc import Mapping
from os import environ

from .config_port import ConfigRepoPort


class EnvConfigRepo(ConfigRepoPort):
    """Adapter: Configuration repository using environment variables."""

    server_host: str
    server_port: int
    ssi_agent_url: str
    awards_service_url: str
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
        self.awards_service_url = env["AWARDS_SERVICE_URL"]
        self.public_url = env["PUBLIC_URL"]
        self.debug = False
        self.postgresql_connection_string = env["POSTGRES_CONNECTION_STRING"]
