"""Unit tests for SsiAgentOffersClientAdapter."""

import pytest

from src.offers.models import Offer
from src.offers.offers_client_port import OfferNotFound, OffersClientError
from src.offers.ssi_agent_offers_client_adapter import SsiAgentOffersClientAdapter
from src.lib.http_client import HttpClient

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
        ssi_agent_url="http://agent.example.com", http_client=http_client
    )


@pytest.fixture
def valid_offer_response() -> MockResponse:
    """Provide a 200 response with valid offer JSON."""
    return MockResponse(status_code=200, _content=_VALID_OFFER_RESPONSE_JSON)


class TestSsiAgentOffersClientAdapter:
    """Tests for the SsiAgentOffersClientAdapter class."""

    def test_get_sends_get_to_correct_url(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
        valid_offer_response: MockResponse,
    ):
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
        http_client.set_response(valid_offer_response)
        result = subject.get("offer-123")
        assert result == Offer(offer_id="offer-123", award_id="", uri=_OFFER_URI)

    def test_get_raises_not_found_on_404(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=404, _content=b'"Not Found"'))
        with pytest.raises(OfferNotFound):
            _ = subject.get("offer-123")

    def test_get_raises_client_error_on_upstream_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
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
        http_client.set_response(MockResponse(status_code=200, _content=b"not json"))
        with pytest.raises(OffersClientError):
            _ = subject.get("offer-123")

    def test_create_posts_credential_then_offer(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        _ = subject.create("offer-123")
        assert http_client.calls[0].method == "post"
        assert http_client.calls[0].url == "http://agent.example.com/v0/credentials"
        assert http_client.calls[1].method == "post"
        assert http_client.calls[1].url == "http://agent.example.com/v0/offers"

    def test_create_returns_uri_from_offer_response(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        # First call (credential): default 200; second call (offer): returns the URI
        http_client.set_response(MockResponse(status_code=200, _content=b""))
        http_client.set_response(
            MockResponse(status_code=200, _content=_OFFER_URI.encode())
        )
        result = subject.create("offer-123")
        assert result == _OFFER_URI

    def test_create_raises_client_error_when_credential_creation_fails(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        http_client.set_response(
            MockResponse(status_code=422, _content=b'"Unprocessable"')
        )
        with pytest.raises(OffersClientError):
            _ = subject.create("offer-123")

    def test_create_raises_client_error_when_offer_creation_fails(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentOffersClientAdapter,
    ):
        # First call (credential) succeeds, second call (offer) fails
        http_client.set_response(MockResponse(status_code=200, _content=b""))
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Server Error"')
        )
        with pytest.raises(OffersClientError):
            _ = subject.create("offer-123")
