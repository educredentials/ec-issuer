"""Configuration management using Ports/Adapters architecture."""

from collections.abc import Mapping
from os import environ


class EnvConfigRepo:
    """Configuration repository using environment variables."""

    server_host: str
    server_port: int
    ssi_agent_url: str
    awards_service_url: str
    debug: bool
    postgresql_connection_string: str
    allowed_cors_domains: str
    credential_configuration_id: str

    def __init__(
        self,
        env: Mapping[str, str] = environ,
        credential_configuration_id: str = "",
    ) -> None:
        """Initialize with optional environment mapping.

        Args:
            env: Environment variable mapping. Defaults to os.environ.
            credential_configuration_id: Pre-resolved credential template ID.
        """
        self.server_host = env["SERVER_HOST"]
        self.server_port = int(env["SERVER_PORT"])
        self.ssi_agent_url = env["SSI_AGENT_URL"]
        self.awards_service_url = env["AWARDS_SERVICE_URL"]
        self.debug = True
        self.postgresql_connection_string = env["POSTGRES_CONNECTION_STRING"]
        self.allowed_cors_domains = env["ALLOWED_CORS_DOMAINS"]
        self.credential_configuration_id = credential_configuration_id
