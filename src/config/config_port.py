from abc import ABC


class ConfigRepoPort(ABC):
    """Port: Configuration repository interface."""

    server_host: str
    server_port: int
    # TODO: Rename to oid4vci_agent_url
    ssi_agent_url: str
    awards_service_url: str
    debug: bool
    postgresql_connection_string: str
    allowed_cors_domains: str
    credential_configuration_id: str
