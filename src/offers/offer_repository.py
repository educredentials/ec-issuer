"""Domain model and port for the offers repository."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Offer:
    """Domain model representing a credential offer."""

    offer_id: str
    achievement_id: str
    uri: str


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
            KeyError: When no offer with the given id exists.
        """
        ...
