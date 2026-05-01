"""Unit tests for PostgreSQLOffersRepository."""

import pytest

from src.offers.offer_repository import Offer, OffersRepositoryPort
from src.offers.postgresql_adapter import PostgreSQLOffersRepository


class TestPostgreSQLOffersRepository:
    """Tests for PostgreSQLOffersRepository."""

    def test_implements_offers_repository_port(self):
        """PostgreSQLOffersRepository implements OffersRepositoryPort."""
        assert issubclass(PostgreSQLOffersRepository, OffersRepositoryPort)

    def test_store_and_get_offer(self, postgresql_connection_string: str):
        """store persists an offer and get retrieves it by id."""
        repo = PostgreSQLOffersRepository(postgresql_connection_string)

        offer = Offer(
            offer_id="test-offer-123",
            achievement_id="award-456",
            uri="openid-credential-offer://?credential_offer_uri=https://issuer.example.com/api/v1/offers/test-offer-123",
            credential_issuer="https://issuer.example.com",
        )

        repo.store(offer)
        result = repo.get("test-offer-123")

        assert result.offer_id == offer.offer_id
        assert result.achievement_id == offer.achievement_id
        assert result.uri == offer.uri
        assert result.credential_issuer == offer.credential_issuer

    def test_get_raises_key_error_for_unknown_id(
        self, postgresql_connection_string: str
    ):
        """get raises KeyError when the offer_id does not exist."""
        repo = PostgreSQLOffersRepository(postgresql_connection_string)

        with pytest.raises(KeyError) as exc_info:
            _ = repo.get("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)

    def test_store_multiple_offers(self, postgresql_connection_string: str):
        """store can persist multiple offers and get retrieves each correctly."""
        repo = PostgreSQLOffersRepository(postgresql_connection_string)

        offer1 = Offer(
            offer_id="offer-1",
            achievement_id="award-1",
            uri="uri-1",
            credential_issuer="issuer-1",
        )
        offer2 = Offer(
            offer_id="offer-2",
            achievement_id="award-2",
            uri="uri-2",
            credential_issuer="issuer-2",
        )

        repo.store(offer1)
        repo.store(offer2)

        result1 = repo.get("offer-1")
        result2 = repo.get("offer-2")

        assert result1.offer_id == offer1.offer_id
        assert result2.offer_id == offer2.offer_id

    def test_store_updates_existing_offer(self, postgresql_connection_string: str):
        """store updates an existing offer with the same id."""
        repo = PostgreSQLOffersRepository(postgresql_connection_string)

        offer1 = Offer(
            offer_id="offer-1",
            achievement_id="award-1",
            uri="uri-1",
            credential_issuer="issuer-1",
        )
        offer2 = Offer(
            offer_id="offer-1",
            achievement_id="award-updated",
            uri="uri-updated",
            credential_issuer="issuer-updated",
        )

        repo.store(offer1)
        repo.store(offer2)

        result = repo.get("offer-1")

        assert result.offer_id == offer2.offer_id
        assert result.achievement_id == offer2.achievement_id
        assert result.uri == offer2.uri
        assert result.credential_issuer == offer2.credential_issuer
