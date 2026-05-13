"""Unit tests for OfferService."""

import pytest

from src.offers.models import Offer
from src.offers.offer_service import (
    DoesNotExistInClientError,
    DoesNotExistInRepositoryError,
    OfferService,
    PermissionDeniedError,
)
from tests.unit.test_doubles import (
    AccessControlSpy,
    AccessControlStub,
    DenyingAccessControlStub,
    OffersClientSpy,
    OffersClientStub,
    OffersClientStubNotFound,
    OffersRepositorySpy,
    OffersRepositoryStub,
    OffersRepositoryStubNotFound,
)

# PUBLIC_URL = "https://issuer.example.com"
ISSUER_AGENT_URL = "http://issuer-agent.example.com"


class TestOfferServiceCreateOffer:
    """Tests for OfferService.create_offer."""

    def test_returns_offer_with_correct_uri_format(self):
        """create_offer returns an Offer URI in the openid-credential-offer scheme."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
        )

        offer = service.create_offer(award_id="award-123", bearer_token="tok")
        assert offer.offer_id is not None
        assert offer.uri is not None
        assert offer.uri.startswith("openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/")

    def test_stores_offer_in_repository(self):
        """create_offer stores offer in offers repository."""
        offers_repository = OffersRepositorySpy()
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=offers_repository,
            offers_client=OffersClientStub(),
        )

        offer = service.create_offer(award_id="award-999", bearer_token="tok")

        # We test against a fixed offer, testing against the return value could
        # give false positives
        expected_offer = Offer(
            offer_id=offer.offer_id,
            award_id="award-999",
            uri=f"openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/{offer.offer_id}"
        )
        assert offers_repository.calls == [("store", {"offer": expected_offer})]

    def test_creates_offer_with_client(self):
        """create_offer creates offer on API with client."""
        offers_client = OffersClientSpy()

        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=offers_client,
        )

        offer = service.create_offer(award_id="award-999", bearer_token="tok")

        assert len(offers_client.calls) == 1
        assert offers_client.calls[0] == (
            "create",
            {"offer_id": offer.offer_id},
        )

    def test_raises_permission_denied_when_access_control_denies(self):
        """create_offer raises PermissionDeniedError when access control denies."""
        service = OfferService(
            access_control=DenyingAccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
        )

        with pytest.raises(PermissionDeniedError):
            _ = service.create_offer(award_id="award-123", bearer_token="tok")

    def test_checks_access_control_with_correct_arguments(self):
        """create_offer passes bearer token and resource details to access control."""

        spy = AccessControlSpy()
        service = OfferService(
            access_control=spy,
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
        )

        _ = service.create_offer(award_id="award-123", bearer_token="my-token")

        assert spy.calls == [("my-token", "award-123", "Award", "import")]


class TestOfferServiceGetOffer:
    """Tests for OfferService.get_offer."""

    def test_get_offer_returns_stored_offer_and_agent_url(self):
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
        )
        result = service.get_offer("offer-123")

        assert result.offer_id == "offer-123"
        assert result.award_id == "award-123"
        assert (
            result.uri
            == "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/offer-123"
        )

    def test_get_offer_raises_does_not_exist_in_repository(self):
        """get_offer raises Error when the offer does not exist in the Repository."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStubNotFound(),
            offers_client=OffersClientStub(),
        )

        with pytest.raises(DoesNotExistInRepositoryError):
            _ = service.get_offer("nonexistent-id")


    def test_get_offer_raises_does_not_exist_in_client(self):
        """get_offer raises Error when the offer does not exist in the Agent."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStubNotFound(),
        )

        with pytest.raises(DoesNotExistInClientError):
            _ = service.get_offer("nonexistent-id")
