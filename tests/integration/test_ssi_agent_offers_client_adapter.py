"""Integration tests for SsiAgentOffersClientAdapter."""

import pytest

from src.offers.offers_client_port import OffersClientPort, OfferNotFound


class TestSsiAgentOffersClientAdapter:
    """Integration tests for SsiAgentOffersClientAdapter."""

    def test_get_offer_by_id(
        self,
        offers_client: OffersClientPort,
    ) -> None:
        """Test get_offer_by_id method."""
        offer = offers_client.get("offer-123")
        assert offer.uri is not None
        assert offer.uri.startswith("openid-credential-offer://?credential_offer_uri")

    def test_get_offer_by_id_not_found(
        self,
        offers_client: OffersClientPort,
    ) -> None:
        """Test get_offer_by_id method when offer is not found."""

        with pytest.raises(OfferNotFound):
            _ = offers_client.get("offer-999")
