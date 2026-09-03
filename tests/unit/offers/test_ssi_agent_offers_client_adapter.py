"""Unit tests for SsiAgentOffersClientAdapter."""

from typing import cast

import pytest

from src.awards.models import (
    Achievement,
    AchievementSubject,
    Criteria,
    EDCAward,
    Issuer,
    OB3Award,
)
from src.lib.http_client import HttpClient
from src.offers.models import Offer
from src.offers.offers_client_port import OfferNotFound, OffersClientError
from src.offers.ssi_agent_offers_client_adapter import SsiAgentOffersClientAdapter

from ..support.requests_doubles import MockResponse, RecordedRequest, RequestsSpy

# Minimal valid JSON that decodes into _SsiAgentOfferResponse.
# The form_url_encoded_credential_offer field is what get() returns as the URI.
_VALID_OFFER_RESPONSE_JSON = (
    b'{"id":"offer-123",'
    b'"grant_types":["urn:ietf:params:oauth:grant-type:pre-authorized_code"],'
    b'"credential_offer_uri":{},'
    b'"credential_offer":{},'
    b'"subject_id":null,'
    b'"credential_ids":[],'
    b'"form_url_encoded_credential_offer":'
    b'"openid-credential-offer://?credential_offer_uri=http%3A%2F%2Fexample.com",'
    b'"pre_authorized_code":"abc123",'
    b'"credential_response":null,'
    b'"status":"PENDING",'
    b'"tx_code":null,'
    b'"delivery_options":null}'
)

_OFFER_URI = "openid-credential-offer://?credential_offer_uri=http%3A%2F%2Fexample.com"


@pytest.fixture
def http_client() -> RequestsSpy:
    """Provide a fresh RequestsSpy for each test."""
    return RequestsSpy()


@pytest.fixture
def subject(http_client: HttpClient) -> SsiAgentOffersClientAdapter:
    """Provide the adapter wired to the spy."""
    return SsiAgentOffersClientAdapter(
        ssi_agent_url="http://agent.example.com",
        credential_template_ids=["openbadge_credential"],
        http_client=http_client,
    )


@pytest.fixture
def valid_offer_response() -> MockResponse:
    """Provide a 200 response with valid offer JSON."""
    return MockResponse(status_code=200, _content=_VALID_OFFER_RESPONSE_JSON)


@pytest.fixture
def sample_award() -> OB3Award:
    """Provide a minimal OB3Award for create_ob3() calls."""
    return OB3Award(
        id="http://example.com/credentials/3527",
        type=["VerifiableCredential", "OpenBadgeCredential"],
        name="Teamwork Badge",
        issuer=Issuer(
            id="https://example.com/issuers/876543",
            type=["Profile"],
            name="Example Corp",
        ),
        validFrom="2010-01-01T00:00:00Z",
        credentialSubject=AchievementSubject(
            id="did:example:ebfeb1f712ebc6f1c276e12ec21",
            type=["AchievementSubject"],
            achievement=Achievement(
                id="https://example.com/achievements/teamwork",
                type=["Achievement"],
                criteria=Criteria(
                    narrative=(
                        "Team members are nominated for this badge by their peers."
                    )
                ),
                description="This badge recognizes the capacity to collaborate.",
                name="Teamwork",
            ),
        ),
    )


class TestSsiAgentOffersClientAdapter:
    """Tests for the SsiAgentOffersClientAdapter class."""

    def test_get_sends_get_to_correct_url(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        valid_offer_response: MockResponse,
    ):
        """get() sends a GET request to the correct SSI agent URL."""
        http_client.set_response(valid_offer_response)
        _ = subject.get("offer-123")
        assert http_client.calls[0] == RecordedRequest(
            method="get",
            url="http://agent.example.com/v0/offers/offer-123",
        )

    def test_get_returns_offer_with_uri_from_response(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        valid_offer_response: MockResponse,
    ):
        """get() returns an Offer with the URI from the agent response."""
        http_client.set_response(valid_offer_response)
        result = subject.get("offer-123")
        assert result == Offer(offer_id="offer-123", award_id="", uri=_OFFER_URI)

    def test_get_raises_not_found_on_404(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        """get() raises OfferNotFound when the agent returns 404."""
        http_client.set_response(MockResponse(status_code=404, _content=b'"Not Found"'))
        with pytest.raises(OfferNotFound):
            _ = subject.get("offer-123")

    def test_get_raises_client_error_on_upstream_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        """get() raises OffersClientError when the agent returns a server error."""
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Server Error"')
        )
        with pytest.raises(OffersClientError):
            _ = subject.get("offer-123")

    def test_get_raises_client_error_on_invalid_response_json(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        """get() raises OffersClientError when the agent returns unparseable JSON."""
        http_client.set_response(MockResponse(status_code=200, _content=b"not json"))
        with pytest.raises(OffersClientError):
            _ = subject.get("offer-123")

    def test_create_ob3_posts_credential_then_offer(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        sample_award: OB3Award,
    ):
        """create_ob3() first POSTs to /v0/credentials then to /v0/offers."""
        _ = subject.create_ob3("offer-123", sample_award)
        assert http_client.calls[0].method == "post"
        assert http_client.calls[0].url == "http://agent.example.com/v0/credentials"
        assert http_client.calls[1].method == "post"
        assert http_client.calls[1].url == "http://agent.example.com/v0/offers"

    def test_create_ob3_returns_uri_from_offer_response(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        sample_award: OB3Award,
    ):
        """create_ob3() returns the URI from the offer creation response."""
        # First call (credential): default 200; second call (offer): returns the URI
        http_client.set_response(MockResponse(status_code=200, _content=b""))
        http_client.set_response(
            MockResponse(status_code=200, _content=_OFFER_URI.encode())
        )
        result = subject.create_ob3("offer-123", sample_award)
        assert result == _OFFER_URI

    def test_create_ob3_raises_client_error_when_credential_creation_fails(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        sample_award: OB3Award,
    ):
        """create_ob3() raises OffersClientError when the credential POST fails."""
        http_client.set_response(
            MockResponse(status_code=422, _content=b'"Unprocessable"')
        )
        with pytest.raises(OffersClientError):
            _ = subject.create_ob3("offer-123", sample_award)

    def test_create_ob3_raises_client_error_when_offer_creation_fails(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        sample_award: OB3Award,
    ):
        """create_ob3() raises OffersClientError when the offer POST fails."""
        # First call (credential) succeeds, second call (offer) fails
        http_client.set_response(MockResponse(status_code=200, _content=b""))
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Server Error"')
        )
        with pytest.raises(OffersClientError):
            _ = subject.create_ob3("offer-123", sample_award)

    def test_create_ob3_uses_credential_template_ids(
        self,
        http_client: RequestsSpy,
        sample_award: OB3Award,
    ):
        """create_ob3() uses the provided credential_template_ids in requests."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["test_credential_config", "european_credential"],
            http_client=http_client,
        )
        _ = adapter.create_ob3("offer-123", sample_award)
        # Check that templateId in credential creation uses first ID
        credential_call = http_client.calls[0]
        assert credential_call.json is not None
        json_dict = cast(dict[str, object], credential_call.json)
        assert isinstance(json_dict, dict)
        assert json_dict["templateId"] == "test_credential_config"
        # Check that templateIds in offer creation uses the full list
        offer_call = http_client.calls[1]
        assert offer_call.json is not None
        offer_dict = cast(dict[str, object], offer_call.json)
        assert isinstance(offer_dict, dict)
        assert offer_dict["offerId"] == "offer-123"
        assert offer_dict["templateIds"] == [
            "test_credential_config",
            "european_credential",
        ]


class TestSsiAgentOffersClientAdapterCreateEDC:
    """Tests for SsiAgentOffersClientAdapter.create_edc()."""

    def test_create_edc_posts_credential_then_offer(
        self,
        http_client: RequestsSpy,
    ):
        """create_edc() first POSTs to /v0/credentials then to /v0/offers."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["openbadge_credential", "european_credential"],
            http_client=http_client,
        )
        edc_award = EDCAward(
            given_name="Learner",
            family_name="Example",
            valid_from="2024-01-01T00:00:00Z",
            learning_achievement={"name": "Badge"},
            awarding_body={"name": "Issuer"},
            awarding_opportunity={"name": "Opportunity"},
            credential_schema={"id": "http://example.com", "type": "sd-jwt_vc+json"},
            subject_id="did:example:subject",
        )
        _ = adapter.create_edc("offer-123", edc_award)
        assert http_client.calls[0].method == "post"
        assert http_client.calls[0].url == "http://agent.example.com/v0/credentials"
        assert http_client.calls[1].method == "post"
        assert http_client.calls[1].url == "http://agent.example.com/v0/offers"

    def test_create_edc_returns_uri_from_offer_response(
        self,
        http_client: RequestsSpy,
    ):
        """create_edc() returns the URI from the offer creation response."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["openbadge_credential", "european_credential"],
            http_client=http_client,
        )
        edc_award = EDCAward(
            given_name="Learner",
            family_name="Example",
            valid_from="2024-01-01T00:00:00Z",
            learning_achievement={"name": "Badge"},
            awarding_body={"name": "Issuer"},
            awarding_opportunity={"name": "Opportunity"},
            credential_schema={"id": "http://example.com", "type": "sd-jwt_vc+json"},
            subject_id="did:example:subject",
        )
        # First call (credential): default 200; second call (offer): returns the URI
        http_client.set_response(MockResponse(status_code=200, _content=b'"ok"'))
        http_client.set_response(
            MockResponse(status_code=200, _content=_OFFER_URI.encode())
        )
        result = adapter.create_edc("offer-123", edc_award)
        assert result == _OFFER_URI

    def test_create_edc_uses_second_template_id(
        self,
        http_client: RequestsSpy,
    ):
        """create_edc() uses the second credential template ID."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["ob3_config", "edc_config"],
            http_client=http_client,
        )
        edc_award = EDCAward(
            given_name="Learner",
            family_name="Example",
            valid_from="2024-01-01T00:00:00Z",
            learning_achievement={"name": "Badge"},
            awarding_body={"name": "Issuer"},
            awarding_opportunity={"name": "Opportunity"},
            credential_schema={"id": "http://example.com", "type": "sd-jwt_vc+json"},
            subject_id="did:example:subject",
        )
        _ = adapter.create_edc("offer-123", edc_award)
        credential_call = http_client.calls[0]
        assert credential_call.json is not None
        json_dict = cast(dict[str, object], credential_call.json)
        assert json_dict["templateId"] == "edc_config"
        offer_call = http_client.calls[1]
        assert offer_call.json is not None
        offer_dict = cast(dict[str, object], offer_call.json)
        assert offer_dict["templateIds"] == ["ob3_config", "edc_config"]

    def test_create_edc_raises_client_error_when_credential_creation_fails(
        self,
        http_client: RequestsSpy,
    ):
        """create_edc() raises OffersClientError when the credential POST fails."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["ob3_config", "edc_config"],
            http_client=http_client,
        )
        edc_award = EDCAward(
            given_name="Learner",
            family_name="Example",
            valid_from="2024-01-01T00:00:00Z",
            learning_achievement={"name": "Badge"},
            awarding_body={"name": "Issuer"},
            awarding_opportunity={"name": "Opportunity"},
            credential_schema={"id": "http://example.com", "type": "sd-jwt_vc+json"},
            subject_id="did:example:subject",
        )
        http_client.set_response(
            MockResponse(status_code=422, _content=b'"Unprocessable"')
        )
        with pytest.raises(OffersClientError):
            _ = adapter.create_edc("offer-123", edc_award)

    def test_create_edc_raises_client_error_when_offer_creation_fails(
        self,
        http_client: RequestsSpy,
    ):
        """create_edc() raises OffersClientError when the offer POST fails."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["ob3_config", "edc_config"],
            http_client=http_client,
        )
        edc_award = EDCAward(
            given_name="Learner",
            family_name="Example",
            valid_from="2024-01-01T00:00:00Z",
            learning_achievement={"name": "Badge"},
            awarding_body={"name": "Issuer"},
            awarding_opportunity={"name": "Opportunity"},
            credential_schema={"id": "http://example.com", "type": "sd-jwt_vc+json"},
            subject_id="did:example:subject",
        )
        # First call (credential) succeeds, second call (offer) fails
        http_client.set_response(MockResponse(status_code=200, _content=b'"ok"'))
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Server Error"')
        )
        with pytest.raises(OffersClientError):
            _ = adapter.create_edc("offer-123", edc_award)

    def test_create_edc_posts_flat_claims_to_credential_endpoint(
        self,
        http_client: RequestsSpy,
    ):
        """create_edc() posts flat dict claims (no nested OB3 structure)."""
        adapter = SsiAgentOffersClientAdapter(
            ssi_agent_url="http://agent.example.com",
            credential_template_ids=["ob3_config", "edc_config"],
            http_client=http_client,
        )
        http_client.set_response(MockResponse(status_code=200, _content=b'"ok"'))
        http_client.set_response(
            MockResponse(status_code=200, _content=_OFFER_URI.encode())
        )
        edc_award = EDCAward(
            given_name="Jan",
            family_name="Jansen",
            valid_from="2024-01-01T00:00:00Z",
            learning_achievement={
                "name": "Badge",
                "description": "A badge",
                "type": "achievement",
            },
            awarding_body={"name": "Issuer", "id": "http://issuer.example.com"},
            awarding_opportunity={"name": "Opportunity"},
            credential_schema={"id": "http://example.com", "type": "sd-jwt_vc+json"},
            subject_id="did:example:subject",
        )
        _ = adapter.create_edc("offer-123", edc_award)
        credential_call = http_client.calls[0]
        assert credential_call.json is not None
        json_dict = cast(dict[str, object], credential_call.json)
        assert isinstance(json_dict, dict)
        credential = cast(dict[str, object], json_dict["credential"])
        assert credential["given_name"] == "Jan"
        assert credential["family_name"] == "Jansen"
        assert "learning_achievement" in credential
        assert "awarding_body" in credential
