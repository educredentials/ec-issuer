from abc import ABC, abstractmethod

from src.offers.models import Offer


class OffersRepositoryPort(ABC):
    """Port: repository interface for persisting and retrieving offers."""

    @abstractmethod
    def store(self, offer: Offer) -> None:
        """Persist an offer.

        Args:
            offer: The offer to store.
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
        """
        ...
