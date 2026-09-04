"""Unit tests for OfferService."""

from dataclasses import asdict

import pytest

from src.offers.models import Offer
from src.offers.offer_service import (
    NotFoundError,
    OfferService,
    OfferServiceError,
    PermissionDeniedError,
    UnknownCredentialTypeError,
)

from ..support.test_doubles import (
    STUB_OB3_AWARD,
    AccessControlSpy,
    AccessControlStub,
    AwardsClientStub,
    CredentialConverterStub,
    DenyingAccessControlStub,
    OffersClientSpy,
    OffersClientStub,
    OffersClientStubNotFound,
    OffersRepositorySpy,
    OffersRepositoryStub,
    OffersRepositoryStubNotFound,
)

# Minimal ELM/EDC credential dict that the converter would return.
_SAMPLE_ELM_CREDENTIAL: dict[str, object] = {
    "@context": ["https://www.w3.org/ns/credentials/v2"],
    "type": ["VerifiableCredential", "EuropeanDigitalCredential"],
    "credentialSubject": {"id": "did:example:subject"},
}

_CONVERTER = CredentialConverterStub(sample_response=_SAMPLE_ELM_CREDENTIAL)

ISSUER_AGENT_URL = "http://issuer-agent.example.com"


class TestOfferServiceCreateOffer:
    """Tests for OfferService.create_offer."""

    def test_returns_offer_with_correct_uri_format(self):
        """create_offer returns an Offer URI in the openid-credential-offer scheme."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        offer = service.create_offer(award_id="award-123", bearer_token="test-token")
        assert offer.offer_id is not None
        assert offer.uri is not None
        assert offer.uri.startswith(
            "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/"
        )

    def test_stores_offer_in_repository(self):
        """create_offer stores offer in offers repository."""
        offers_repository = OffersRepositorySpy()
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=offers_repository,
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        offer = service.create_offer(award_id="award-999", bearer_token="test-token")

        # We test against a fixed offer, testing against the return value could
        # give false positives
        expected_offer = Offer(
            offer_id=offer.offer_id,
            award_id="award-999",
            uri=f"openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/{offer.offer_id}",
        )
        assert offers_repository.calls == [("store", {"offer": expected_offer})]

    def test_creates_offer_with_client(self):
        """create_offer creates offer on API with client, passing the fetched award."""
        offers_client = OffersClientSpy()

        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=offers_client,
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        offer = service.create_offer(award_id="award-999", bearer_token="test-token")

        assert len(offers_client.calls) == 1
        assert offers_client.calls[0] == (
            "create_ob3",
            {"offer_id": offer.offer_id, "award": STUB_OB3_AWARD},
        )

    def test_raises_permission_denied_when_access_control_denies(self):
        """create_offer raises PermissionDeniedError when access control denies."""
        service = OfferService(
            access_control=DenyingAccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        with pytest.raises(PermissionDeniedError):
            _ = service.create_offer(award_id="award-123", bearer_token="test-token")

    def test_checks_access_control_with_correct_arguments(self):
        """create_offer passes bearer token and resource details to access control."""

        spy = AccessControlSpy()
        service = OfferService(
            access_control=spy,
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        _ = service.create_offer(award_id="award-123", bearer_token="my-token")

        assert spy.calls == [("my-token", "award-123", "Award", "import")]

    def test_create_offer_dispatches_create_edc_when_credential_type_is_edc(
        self,
    ):
        """create_offer with credential_type='edc' dispatches to create_edc."""
        offers_client = OffersClientSpy()

        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=offers_client,
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        _ = service.create_offer(
            award_id="award-999",
            bearer_token="test-token",
            credential_type="edc",
        )

        assert len(offers_client.calls) == 1
        call_name, call_args = offers_client.calls[0]
        assert call_name == "create_edc"
        assert call_args["offer_id"] is not None
        assert call_args["credential"] == _SAMPLE_ELM_CREDENTIAL

    def test_edc_path_converts_ob3_award_through_converter(self):
        """EDC path calls the converter with the OB3 award,
        passes result to create_edc."""
        converter = CredentialConverterStub(sample_response=_SAMPLE_ELM_CREDENTIAL)
        offers_client = OffersClientSpy()

        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=offers_client,
            awards_client=AwardsClientStub(),
            credential_converter=converter,
        )

        _ = service.create_offer(
            award_id="award-999",
            bearer_token="test-token",
            credential_type="edc",
        )

        # Converter should have received the OB3 award as dict
        assert converter.calls == [
            ("convert", {"credential": asdict(STUB_OB3_AWARD)})
        ]

        # create_edc should have received the converter's output
        call_name, call_args = offers_client.calls[0]
        assert call_name == "create_edc"
        assert call_args["credential"] == _SAMPLE_ELM_CREDENTIAL


class TestOfferServiceGetOffer:
    """Tests for OfferService.get_offer."""

    def test_get_offer_returns_stored_offer_and_agent_url(self):
        """get_offer returns Offer with URI from the client and award_id from repo."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )
        result = service.get_offer("offer-123")

        assert result.offer_id == "offer-123"
        assert result.award_id == "award-123"
        assert (
            result.uri
            == "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/offer-123"
        )

    def test_get_offer_raises_not_found_when_offer_absent_in_client(self):
        """get_offer raises NotFoundError when the offer is absent in the SSI agent."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStubNotFound(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        with pytest.raises(NotFoundError, match="Offer nonexistent-id not found"):
            _ = service.get_offer("nonexistent-id")

    def test_get_offer_raises_not_found_when_offer_absent_in_repository(self):
        """get_offer raises NotFoundError when the offer is absent in the repository."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStubNotFound(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        with pytest.raises(NotFoundError, match="Offer nonexistent-id not found"):
            _ = service.get_offer("nonexistent-id")

    def test_get_offer_raises_offer_service_error_on_client_error(self):
        """get_offer raises OfferServiceError when the SSI agent returns an error."""
        from typing import override

        from src.offers.offers_client_port import OffersClientError

        class _OffersClientErrorStub(OffersClientStub):
            @override
            def get(self, offer_id: str) -> Offer:
                raise OffersClientError("upstream failure")

        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=_OffersClientErrorStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        with pytest.raises(OfferServiceError):
            _ = service.get_offer("test-123")


class TestOfferServiceCreateOfferCredentialType:
    """Tests for credential_type validation in create_offer."""

    def test_raises_unknown_credential_type_for_invalid_value(self):
        """create_offer raises UnknownCredentialTypeError for unsupported values."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        with pytest.raises(
            UnknownCredentialTypeError, match="Unsupported credential_type"
        ):
            _ = service.create_offer(
                award_id="award-123",
                bearer_token="test-token",
                credential_type="unsupported",
            )

    def test_edc_credential_type_rejected_when_invalid(self):
        """create_offer rejects 'EDC' (capitalized) and other case variants."""
        service = OfferService(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            awards_client=AwardsClientStub(),
            credential_converter=_CONVERTER,
        )

        with pytest.raises(UnknownCredentialTypeError):
            _ = service.create_offer(
                award_id="award-123",
                bearer_token="test-token",
                credential_type="EDC",
            )
