"""Integration tests for PostgreSQLOffersRepository."""

import pytest

from src.offers.models import Offer
from src.offers.offers_repository_port import OffersRepositoryPort
from src.offers.postgresql_offers_repository_adapter import (
    PostgreSQLOffersRepositoryAdapter,
)


class TestPostgreSQLOffersRepository:
    """Tests for PostgreSQLOffersRepository."""

    def test_implements_offers_repository_port(self):
        """PostgreSQLOffersRepository implements OffersRepositoryPort."""
        assert issubclass(PostgreSQLOffersRepositoryAdapter, OffersRepositoryPort)

    def test_store_and_get_offer(self, offers_repo: PostgreSQLOffersRepositoryAdapter):
        """store persists an offer and get retrieves it by id."""
        offer = Offer(offer_id="offer-123", award_id="award-456", uri=None)

        offers_repo.store(offer)
        result = offers_repo.get("offer-123")

        assert result.offer_id == offer.offer_id
        assert result.award_id == offer.award_id

    def test_get_raises_key_error_for_unknown_id(
        self, offers_repo: PostgreSQLOffersRepositoryAdapter
    ):
        """get raises KeyError when the offer_id does not exist."""
        with pytest.raises(KeyError) as exc_info:
            _ = offers_repo.get("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)

    def test_store_multiple_offers(
        self, offers_repo: PostgreSQLOffersRepositoryAdapter
    ):
        """store can persist multiple offers and get retrieves each correctly."""
        offer1 = Offer(offer_id="offer-1", award_id="award-123", uri=None)
        offer2 = Offer(offer_id="offer-2", award_id="award-123", uri=None)

        offers_repo.store(offer1)
        offers_repo.store(offer2)

        result1 = offers_repo.get("offer-1")
        result2 = offers_repo.get("offer-2")

        assert result1.offer_id == offer1.offer_id
        assert result1.award_id == offer1.award_id
        assert result2.offer_id == offer2.offer_id
        assert result2.award_id == offer2.award_id

    def test_store_updates_existing_offer(
        self, offers_repo: PostgreSQLOffersRepositoryAdapter
    ):
        """store updates an existing offer with the same id."""
        offer1 = Offer(offer_id="offer-1", award_id="award-123", uri=None)
        offer2 = Offer(offer_id="offer-1", award_id="award-updated", uri=None)

        offers_repo.store(offer1)
        offers_repo.store(offer2)

        result = offers_repo.get("offer-1")

        assert result.offer_id == "offer-1"
        assert result.award_id == "award-updated"
