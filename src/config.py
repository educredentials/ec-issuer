"""Configuration management using Ports/Adapters architecture."""

from os import environ
from typing import Protocol

from typing_extensions import Mapping


class ConfigRepo(Protocol):
    """Port: Configuration repository interface."""

    server_host: str
    server_port: int


class EnvConfigRepo:
    """Adapter: Configuration repository using environment variables."""

    server_host: str
    server_port: int

    def __init__(self, env: Mapping[str, str] = environ):
        """Initialize with optional environment mapping.

        Args:
            env: Environment variable mapping. Defaults to os.environ.
        """
        self.server_host = env["SERVER_HOST"]
        self.server_port = int(env["SERVER_PORT"])
