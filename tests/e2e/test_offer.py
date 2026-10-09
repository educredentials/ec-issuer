"""End-to-end tests for offer endpoints."""

from dataclasses import asdict, dataclass
from urllib.parse import parse_qs, urlparse

import msgspec
import pytest

from tests.e2e.support.admin_client import AdminHttpClient
from tests.e2e.support.config import Config
from tests.e2e.support.http_client import HttpClient
from tests.e2e.support.utilities import assert_schema


@dataclass
class AuthorizationCodeGrant:
    authorization_code: dict[str, str]


@dataclass
class Offer:
    credential_issuer: str
    credential_configuration_ids: list[str]
    grants: AuthorizationCodeGrant


@dataclass
class CreateOfferResponse:
    offer_id: str
    uri: str


@pytest.mark.e2e
class TestOffer:
    """Test the offer endpoint."""

    @pytest.mark.parametrize(
        "credential_type",
        ["ob3", "edc"],
    )
    def test_create_offer(
        self,
        admin_client: AdminHttpClient,
        config: Config,
        credential_type: str,
    ):
        """Test that POST /api/v1/offers creates an offer and returns URI + offer_id."""
        create_offer_response = admin_client.create_offer(
            award_id="award-123", credential_type=credential_type
        )
        assert_schema(asdict(create_offer_response), "create_offer_response")

        uri = create_offer_response.uri
        # Fixed in mock-ssi-agent. Should be the uuid in create_offer_response.offer_id
        offer_id = "offer-123"
        parsed: str = parse_qs(urlparse(uri).query)["credential_offer_uri"][0]
        assert parsed == f"{config.ssi_agent_url}/openid4vci/offers/{offer_id}"

    @pytest.mark.parametrize(
        "credential_type",
        ["ob3", "edc"],
    )
    def test_get_offer(
        self,
        admin_client: AdminHttpClient,
        http_client: HttpClient,
        config: Config,
        credential_type: str,
    ):
        """Test that GET credential_offer_uri returns a credential offer object."""
        create_response = admin_client.create_offer(
            award_id="award-123", credential_type=credential_type
        )
        credential_offer_uri: str = parse_qs(urlparse(create_response.uri).query)[
            "credential_offer_uri"
        ][0]
        response = http_client.get(credential_offer_uri)

        assert response.status_code == 200
        offer = msgspec.json.decode(response.text, type=Offer)

        # A valid credential offer object
        assert_schema(asdict(offer), "credential_offer")
        # The issuer is the expected openid4vci-agent
        assert offer.credential_issuer == config.ssi_agent_url

    @pytest.mark.parametrize(
        "credential_type",
        ["ob3", "edc"],
    )
    def test_offer_is_authorization_code_flow(
        self,
        admin_client: AdminHttpClient,
        http_client: HttpClient,
        credential_type: str,
    ):
        """Test that a credential offer has attributes for authorization code flow."""
        create_response = admin_client.create_offer(
            award_id="award-123", credential_type=credential_type
        )
        credential_offer_uri: str = parse_qs(urlparse(create_response.uri).query)[
            "credential_offer_uri"
        ][0]
        response = http_client.get(credential_offer_uri)
        offer = msgspec.json.decode(response.text, type=Offer)

        assert offer.grants.authorization_code["issuer_state"] != ""
