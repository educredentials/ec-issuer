"""End-to-end tests for offer endpoints."""

from urllib.parse import parse_qs, urlparse

import pytest

from tests.e2e.conftest import Config, HttpClient, assert_schema, jsonpath_value


@pytest.mark.e2e
class TestOffer:
    """Test the offer endpoint."""

    def test_create_offer(self, e2e_client: HttpClient, config: Config):
        """Test that POST /api/v1/offers creates an offer and returns URI + offer_id."""
        response = e2e_client.post(
            "api/v1/offers",
            json={"achievement_id": "award-123"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text[:200]}"
        )
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "create_offer_response")

        offer_id = jsonpath_value(body, "$.offer_id")
        uri = jsonpath_value(body, "$.uri")
        assert uri == (
            f"openid-credential-offer://?credential_offer_uri={config.public_url}/api/v1/offers/{offer_id}"
        )

    def test_get_offer(self, e2e_client: HttpClient, config: Config):
        """Test that GET /api/v1/offers/<offer_id> returns a credential offer object."""
        create_response = e2e_client.post(
            "api/v1/offers",
            json={"achievement_id": "award-123"},
            headers={"Authorization": "Bearer test-token"},
        )
        create_body: object = create_response.json()  # pyright: ignore[reportAny]
        offer_uri: str = jsonpath_value(create_body, "$.uri")  # pyright: ignore[reportAssignmentType]

        credential_offer_uri: str = parse_qs(urlparse(offer_uri).query)[
            "credential_offer_uri"
        ][0]
        offer_path = urlparse(credential_offer_uri).path.lstrip("/")

        response = e2e_client.get(offer_path)

        assert response.status_code == 200
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "credential_offer")
        assert jsonpath_value(body, "$.credential_issuer") == config.public_url
