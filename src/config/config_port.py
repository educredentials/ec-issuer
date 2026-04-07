from abc import ABC


class ConfigRepoPort(ABC):
    """Port: Configuration repository interface."""

    server_host: str
    server_port: int
    issuer_agent_base_url: str
    debug: bool
