"""Domain model and port for the offers repository."""

from abc import ABC, abstractmethod

from src.offers.models import Offer

class OfferNotFound(Exception):
    """Error raised when API service returns 404"""


class OffersClientError(Exception):
    """Error raised when API service returns a non-404 error"""


class OffersClientPort(ABC):
    """Port: repository interface for persisting and retrieving offers."""

    # TODO: Award is not appropriate here. We want a decoupled abstraction.
    # Maybe something like "CredentialPayload"? That can be built from the Award.
    # So maybe we can build that here?

    @abstractmethod
    def create(self, offer_id: str) -> str:
        """Persist an offer.

        Args:
            offer: The offer to store.

        Returns:
            The offer URI
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
            KeyError: When no offer with the given id exists.
        """
        ...
