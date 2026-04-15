"""In-memory adapter for the offers repository."""

from typing import override

from src.offers.offer_service import Offer, OffersRepositoryPort


class InMemoryOffersRepository(OffersRepositoryPort):
    """Adapter that stores offers in memory for the lifetime of the process."""

    def __init__(self) -> None:
        """Initialise with an empty store."""
        self._store: dict[str, Offer] = {}

    @override
    def store(self, offer: Offer) -> None:
        """Persist an offer in memory.

        Args:
            offer: The offer to store.
        """
        self._store[offer.offer_id] = offer

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            KeyError: When no offer with the given id exists.
        """
        return self._store[offer_id]
