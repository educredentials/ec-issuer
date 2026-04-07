"""API Adapter module."""

from abc import ABC, abstractmethod

from src.config.config_port import ConfigRepoPort
from src.metadata.metadata import MetadataService


class ApiPort(ABC):
    """API Protocol."""

    metadata_service: MetadataService

    @abstractmethod
    def __init__(
        self, config: ConfigRepoPort, metadata_service: MetadataService
    ) -> None:
        """Initialize the API."""
        ...

    @abstractmethod
    def run(self):
        """Run the API daemon"""
        ...
