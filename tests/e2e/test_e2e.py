"""End-to-end tests for the EC Issuer."""

import unittest

import pytest

from tests.e2e.conftest import TestClient


@pytest.mark.e2e
class TestHealthEndpoint:
    """Test the health endpoint."""

    def test_health_success(self, e2e_client: TestClient):
        """Test that the health endpoint returns OK."""
        response = e2e_client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"


@pytest.mark.e2e
class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_endpoint(self, e2e_client: TestClient):
        """Test that the root endpoint returns Hello, World!."""
        response = e2e_client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"


@pytest.mark.e2e
class TestCredentialIssuerMetadataEndpoint:
    """Test the Credential Issuer Metadata endpoint."""

    def test_credential_issuer_metadata_returns_correct_json(
        self, e2e_client: TestClient
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
