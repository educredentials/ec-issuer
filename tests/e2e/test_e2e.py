"""End-to-end tests for the EC Issuer."""

from urllib.parse import parse_qs, urlparse

import pytest

from tests.e2e.conftest import Config, HttpClient, assert_schema, jsonpath_value


@pytest.mark.e2e
class TestHealthEndpoint:
    """Test the health endpoint."""

    def test_health_success(self, e2e_client: HttpClient):
        """Test that the health endpoint returns OK."""
        response = e2e_client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"


@pytest.mark.e2e
class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_endpoint(self, e2e_client: HttpClient):
        """Test that the root endpoint returns Hello, World!."""
        response = e2e_client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"


@pytest.mark.e2e
class TestCredentialIssuerMetadataEndpoint:
    """Test the Credential Issuer Metadata endpoint."""

    def test_credential_issuer_metadata_returns_correct_json(
        self, e2e_client: HttpClient
    ):
        """Test Credential Issuer Metadata endpoint returns correct JSON."""
        response = e2e_client.get("/.well-known/openid-credential-issuer")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "credential_issuer_metadata")
        assert (
            jsonpath_value(body, "$.credential_issuer") == "https://issuer.example.com"
        )
        assert (
            jsonpath_value(body, "$.credential_endpoint")
            == "https://issuer.example.com/credential"
        )
        assert (
            jsonpath_value(body, "$.authorization_servers[0]")
            == "https://authn.example.com"
        )


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


@pytest.mark.e2e
class TestMetricsEndpoint:
    """Test the Prometheus metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_metrics(self, e2e_client: HttpClient):
        """Test that /metrics endpoint returns Prometheus metrics after requesting /."""
        response = e2e_client.get("/")
        assert response.status_code == 200

        response = e2e_client.get("/metrics")
        assert response.status_code == 200

        text = response.text
        assert 'flask_http_request_total{method="GET",status="200"}' in text
        assert (
            "TYPE" in text
            or "COUNTER" in text
            or "GAUGE" in text
            or "HISTOGRAM" in text
            or "SUMMARY" in text
        )
