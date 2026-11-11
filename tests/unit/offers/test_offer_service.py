"""Unit tests for OfferService."""

from typing import override

from src.awards.awards_client_port import AwardsClientPort
from src.awards.models import ob3_award_to_json_dict
from src.credential_converter.credential_converter_port import (
    CredentialConverterPort,
)
from src.offers.offers_client_port import OffersClientPort
from src.offers.offers_repository_port import OffersRepositoryPort

import pytest

from src.access_control.access_control_port import AccessControlPort
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


def _make_service(
    *,
    access_control: AccessControlPort | None = None,
    awards_client: AwardsClientPort | None = None,
    offers_repository: OffersRepositoryPort | None = None,
    offers_client: OffersClientPort | None = None,
    credential_converter: CredentialConverterPort | None = None,
) -> OfferService:
    """Build an OfferService on standard stubs, with per-dependency overrides.

    Stubs are created fresh per call so recorded calls never leak between tests.
    """
    return OfferService(
        access_control=access_control or AccessControlStub(),
        offers_repository=offers_repository or OffersRepositoryStub(),
        offers_client=offers_client or OffersClientStub(),
        awards_client=awards_client or AwardsClientStub(),
        credential_converter=credential_converter
        or CredentialConverterStub(sample_response=_SAMPLE_ELM_CREDENTIAL),
    )


ISSUER_AGENT_URL = "http://issuer-agent.example.com"


class TestOfferServiceCreateOffer:
    """Tests for OfferService.create_offer."""

    def test_returns_offer_with_correct_uri_format(self):
        """create_offer returns an Offer URI in the openid-credential-offer scheme."""
        service = _make_service()

        offer = service.create_offer(award_id="award-123", bearer_token="test-token")
        assert offer.offer_id is not None
        assert offer.uri is not None
        assert offer.uri.startswith(
            "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/"
        )

    def test_stores_offer_in_repository(self):
        """create_offer stores offer in offers repository."""
        offers_repository = OffersRepositorySpy()
        service = _make_service(offers_repository=offers_repository)

        offer = service.create_offer(award_id="award-999", bearer_token="test-token")

        assert len(offers_repository.calls) == 1
        _, kwargs = offers_repository.calls[0]
        stored_offer = kwargs["offer"]
        assert stored_offer.offer_id == offer.offer_id
        assert stored_offer.award_id == "award-999"
        assert stored_offer.uri == offer.uri
        assert stored_offer.credential_ids == []
        assert stored_offer.created_at is not None

    def test_creates_offer_with_client(self):
        """create_offer creates offer on API with client, passing the fetched award."""
        offers_client = OffersClientSpy()

        service = _make_service(offers_client=offers_client)

        offer = service.create_offer(award_id="award-999", bearer_token="test-token")

        assert len(offers_client.calls) == 1
        assert offers_client.calls[0] == (
            "create_ob3",
            {"offer_id": offer.offer_id, "award": STUB_OB3_AWARD},
        )

    def test_raises_permission_denied_when_access_control_denies(self):
        """create_offer raises PermissionDeniedError when access control denies."""
        service = _make_service(access_control=DenyingAccessControlStub())

        with pytest.raises(PermissionDeniedError):
            _ = service.create_offer(award_id="award-123", bearer_token="test-token")

    def test_checks_access_control_with_correct_arguments(self):
        """create_offer passes bearer token and resource details to access control."""

        spy = AccessControlSpy()
        service = _make_service(access_control=spy)

        _ = service.create_offer(award_id="award-123", bearer_token="my-token")

        assert spy.calls == [("my-token", "award-123", "Award", "import")]

    def test_create_offer_dispatches_create_edc_when_credential_type_is_edc(
        self,
    ):
        """create_offer with credential_type='edc' dispatches to create_edc."""
        offers_client = OffersClientSpy()

        service = _make_service(offers_client=offers_client)

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

        service = _make_service(
            offers_client=offers_client, credential_converter=converter
        )

        _ = service.create_offer(
            award_id="award-999",
            bearer_token="test-token",
            credential_type="edc",
        )

        # Converter should have received the OB3 award as dict (nulls filtered)
        assert converter.calls == [
            ("convert", {"credential": ob3_award_to_json_dict(STUB_OB3_AWARD)})
        ]

        # create_edc should have received the converter's output
        call_name, call_args = offers_client.calls[0]
        assert call_name == "create_edc"
        assert call_args["credential"] == _SAMPLE_ELM_CREDENTIAL


class TestOfferServiceGetOffer:
    """Tests for OfferService.get_offer."""

    def test_get_offer_returns_stored_offer_and_agent_url(self):
        """get_offer returns Offer with URI from the client and award_id from repo."""
        service = _make_service()
        result = service.get_offer("offer-123")

        assert result.offer_id == "offer-123"
        assert result.award_id == "award-123"
        assert (
            result.uri
            == "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/offer-123"
        )

    def test_get_offer_raises_not_found_when_offer_absent_in_client(self):
        """get_offer raises NotFoundError when the offer is absent in the SSI agent."""
        service = _make_service(offers_client=OffersClientStubNotFound())

        with pytest.raises(NotFoundError, match="Offer nonexistent-id not found"):
            _ = service.get_offer("nonexistent-id")

    def test_get_offer_raises_not_found_when_offer_absent_in_repository(self):
        """get_offer raises NotFoundError when the offer is absent in the repository."""
        service = _make_service(offers_repository=OffersRepositoryStubNotFound())

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

        service = _make_service(offers_client=_OffersClientErrorStub())

        with pytest.raises(OfferServiceError):
            _ = service.get_offer("test-123")


class TestOfferServiceTransactionRollback:
    """Tests for transaction rollback on store failure."""

    def test_rollback_called_when_repository_store_fails(self):
        """create_offer rolls back the client when repository store raises."""

        class _FailingRepositoryStub(OffersRepositoryStub):
            """Stub that raises on store to simulate a transient failure."""

            @override
            def store(self, offer: Offer) -> None:
                """Raise an exception to simulate a transient failure."""
                raise RuntimeError("transient db failure")

        offers_client = OffersClientSpy()
        service = _make_service(
            offers_repository=_FailingRepositoryStub(), offers_client=offers_client
        )

        with pytest.raises(RuntimeError, match="transient db failure"):
            _ = service.create_offer(award_id="award-42", bearer_token="test-token")

        # Verify create_ob3 was called first, then rollback was called
        assert len(offers_client.calls) == 2
        assert offers_client.calls[0][0] == "create_ob3"
        assert offers_client.calls[1][0] == "rollback"
        offer_id = offers_client.calls[0][1]["offer_id"]
        assert offers_client.calls[1][1] == {"offer_id": offer_id}


class TestOfferServiceCreateOfferCredentialType:
    """Tests for credential_type validation in create_offer."""

    def test_raises_unknown_credential_type_for_invalid_value(self):
        """create_offer raises UnknownCredentialTypeError for unsupported values."""
        service = _make_service()

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
        service = _make_service()

        with pytest.raises(UnknownCredentialTypeError):
            _ = service.create_offer(
                award_id="award-123",
                bearer_token="test-token",
                credential_type="EDC",
            )
