"""Configuration management using Ports/Adapters architecture."""

from collections.abc import Mapping
from os import environ

from src.config.config_port import ConfigRepoPort

class EnvConfigRepo(ConfigRepoPort):
    """Adapter: Configuration repository using environment variables."""

    server_host: str
    server_port: int
    issuer_agent_base_url: str
    debug: bool

    def __init__(self, env: Mapping[str, str] = environ):
        """Initialize with optional environment mapping.

        Args:
            env: Environment variable mapping. Defaults to os.environ.
        """
        self.server_host = env["SERVER_HOST"]
        self.server_port = int(env["SERVER_PORT"])
        self.issuer_agent_base_url = env["ISSUER_AGENT_BASE_URL"]
        self.debug = False
