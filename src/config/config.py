"""Configuration management using Ports/Adapters architecture."""

from collections.abc import Mapping
from os import environ

from src.offers.models import CredentialType


class EnvConfigRepo:
    """Configuration repository using environment variables."""

    server_host: str
    server_port: int
    ssi_agent_url: str
    edc_ssi_agent_url: str
    awards_service_url: str
    debug: bool
    postgresql_connection_string: str
    allowed_cors_domains: str
    ec_issuer_url: str
    ec_issuer_extensions_dir: str
    credential_configuration_ids: dict[CredentialType, str]
    credential_converter_url: str

    def __init__(
        self,
        env: Mapping[str, str] = environ,
        credential_configuration_ids: dict[CredentialType, str] | None = None,
    ) -> None:
        """Initialize with optional environment mapping.

        Args:
            env: Environment variable mapping. Defaults to os.environ.
            credential_configuration_ids: Pre-resolved credential template IDs.
        """
        self.server_host = env["SERVER_HOST"]
        self.server_port = int(env["SERVER_PORT"])
        self.ssi_agent_url = env["SSI_AGENT_URL"]
        self.edc_ssi_agent_url = env.get(
            "SSI_AGENT_EDC_URL", self.ssi_agent_url
        )
        self.awards_service_url = env["AWARDS_SERVICE_URL"]
        self.credential_converter_url = env["CREDENTIAL_CONVERTER_URL"]
        self.debug = env.get("DEBUG", "false").lower() in ("true", "1", "yes")
        self.postgresql_connection_string = env["POSTGRES_CONNECTION_STRING"]
        self.allowed_cors_domains = env["ALLOWED_CORS_DOMAINS"]
        self.ec_issuer_url = env.get("EC_ISSUER_URL", "http://localhost:8000")
        self.ec_issuer_extensions_dir = env.get(
            "EC_ISSUER_EXTENSIONS_DIR", "/static/extensions"
        )
        self.credential_configuration_ids = credential_configuration_ids or {}
