from abc import ABC


class ConfigRepoPort(ABC):
    """Port: Configuration repository interface."""

    server_host: str
    server_port: int
    issuer_agent_base_url: str
    public_url: str
    debug: bool
    postgresql_connection_string: str
