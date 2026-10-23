"""Domain model and port for the offers repository."""

from abc import ABC, abstractmethod

from src.awards.models import OB3Award

from .models import Offer


class OfferNotFound(Exception):
    """Error raised when API service returns 404"""


class OffersClientError(Exception):
    """Error raised when API service returns a non-404 error"""


class OffersClientPort(ABC):
    """Port: repository interface for persisting and retrieving offers."""

    @abstractmethod
    def create_ob3(self, offer_id: str, award: OB3Award) -> str:
        """Create an OB3 credential offer on the SSI agent.

        Args:
            offer_id: The offer identifier to create.
            award: The OB3 AchievementCredential to issue.

        Returns:
            The offer URI.
        """
        ...

    @abstractmethod
    def create_edc(
        self, offer_id: str, credential: dict[str, object]
    ) -> str:
        """Create an EDC credential offer on the SSI agent.

        Args:
            offer_id: The offer identifier to create.
            credential: The ELM/EDC credential as a dict.

        Returns:
            The offer URI.
        """
        ...

    @abstractmethod
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            OfferNotFound: When no offer with the given id exists.
            OffersClientError: When the upstream service returns an error.
        """
        ...
