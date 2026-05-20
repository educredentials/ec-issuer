"""API Adapter module."""

from abc import ABC, abstractmethod

from src.config.config_port import ConfigRepoPort
from src.offers.offer_service import OfferService


class ApiPort(ABC):
    """API Protocol."""

    offer_service: OfferService

    @abstractmethod
    def __init__(
        self,
        config: ConfigRepoPort,
        offer_service: OfferService,
    ) -> None:
        """Initialize the API."""
        ...

    @abstractmethod
    def run(self):
        """Run the API daemon"""
        ...
