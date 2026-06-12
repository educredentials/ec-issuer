"""Domain model and port for the offers repository."""

from abc import ABC, abstractmethod

from src.awards.models import Award

from .models import Offer


class OfferNotFound(Exception):
    """Error raised when API service returns 404"""


class OffersClientError(Exception):
    """Error raised when API service returns a non-404 error"""


class OffersClientPort(ABC):
    """Port: repository interface for persisting and retrieving offers."""

    @abstractmethod
    def create(self, offer_id: str, award: Award) -> str:
        """Create a credential offer on the SSI agent.

        Args:
            offer_id: The offer identifier to create.
            award: The award (OB3 AchievementCredential) for this offer.

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
