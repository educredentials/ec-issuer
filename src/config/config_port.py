from abc import ABC


class ConfigRepoPort(ABC):
    """Port: Configuration repository interface."""

    server_host: str
    server_port: int
    ssi_agent_url: str
    ssi_agent_nonce_endpoint: str
    ssi_agent_credential_endpoint: str
    public_url: str
    debug: bool
    postgresql_connection_string: str
