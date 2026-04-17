"""End-to-end tests for the EC Issuer."""

import unittest
from urllib.parse import parse_qs, urlparse

import pytest

from tests.e2e.conftest import Config, HttpClient


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
        unittest.TestCase().assertDictEqual(
            response.json(),  # pyright: ignore[reportAny], json can be any type by design here
            {
                "authorization_servers": ["https://authn.example.com"],
                "credential_configurations_supported": {},
                "credential_endpoint": "https://issuer.example.com/credential",
                "credential_issuer": "https://issuer.example.com",
            },
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
        body: dict[str, str] = response.json()  # pyright: ignore[reportAny] json can be any type by design here
        assert "offer_id" in body
        assert "uri" in body
        offer_id: str = body["offer_id"]

        assert config.public_url in body["uri"]

        expected_credential_offer_uri: str = (
            f"{config.public_url}/api/v1/offers/{offer_id}"
        )
        assert body["uri"] == (
            f"openid-credential-offer://?credential_offer_uri={expected_credential_offer_uri}"
        )

    def test_get_offer(self, e2e_client: HttpClient):
        """Test that GET /api/v1/offers/<offer_id> returns the full offer as JSON."""
        create_response = e2e_client.post(
            "api/v1/offers",
            json={"achievement_id": "award-123"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert create_response.status_code == 201
        create_body: dict[str, str] = create_response.json()  # pyright: ignore[reportAny]
        offer_uri: str = create_body["uri"]

        credential_offer_uri: str = parse_qs(urlparse(offer_uri).query)[
            "credential_offer_uri"
        ][0]
        offer_path = urlparse(credential_offer_uri).path

        response = e2e_client.get(offer_path.lstrip("/"))

        assert response.status_code == 200
        body: dict[str, str] = response.json()  # pyright: ignore[reportAny]
        assert body["offer_id"] == create_body["offer_id"]
        assert body["achievement_id"] == "award-123"
        assert "uri" in body


@pytest.mark.e2e
class TestMetricsEndpoint:
    """Test the Prometheus metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_metrics(self, e2e_client: HttpClient):
        """Test that /metrics endpoint returns Prometheus metrics after requesting /."""
        # First request the root endpoint to generate metrics
        response = e2e_client.get("/")
        assert response.status_code == 200

        # Then request the metrics endpoint
        response = e2e_client.get("/metrics")
        assert response.status_code == 200

        # Verify it contains Prometheus-style metrics
        text = response.text
        assert 'flask_http_request_total{method="GET",status="200"}' in text
        assert (
            "TYPE" in text
            or "COUNTER" in text
            or "GAUGE" in text
            or "HISTOGRAM" in text
            or "SUMMARY" in text
        )
