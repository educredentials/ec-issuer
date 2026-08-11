"""Configuration port — defines the interface for configuration repositories."""

from typing import Protocol


class ConfigRepoPort(Protocol):
    """Port: Configuration repository interface."""

    server_host: str
    server_port: int
    ssi_agent_url: str
    awards_service_url: str
    debug: bool
    postgresql_connection_string: str
    allowed_cors_domains: str
    credential_configuration_id: str
