"""Configuration management for the EC Issuer Flask application."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration from environment variables."""

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        return cls(
            server_host=os.environ.get("SERVER_HOST", "0.0.0.0"),
            server_port=int(os.environ.get("SERVER_PORT", "8000"))
        )
