"""API Adapter module."""

from abc import ABC, abstractmethod

from src.config import ConfigRepo
from src.metadata import MetadataService


class ApiPort(ABC):
    """API Protocol."""

    metadata_service: MetadataService

    @abstractmethod
    def __init__(self, config: ConfigRepo, metadata_service: MetadataService) -> None:
        """Initialize the API."""
        ...

    @abstractmethod
    def run(self):
        """Run the API daemon"""
        ...
