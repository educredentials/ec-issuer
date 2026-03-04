"""End-to-end tests for the Flask-based EC Issuer."""

import pytest


@pytest.mark.e2e
class TestHealthEndpoint:
    """Test the health endpoint."""

    def test_health_success(self, client):
        """Test that the health endpoint returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.data == b"OK"


@pytest.mark.e2e
class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_endpoint(self, client):
        """Test that the root endpoint returns Hello, World!."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.data == b"Hello, World!"


@pytest.mark.e2e
class TestCredentialIssuerMetadataEndpoint:
    """Test the Credential Issuer Metadata endpoint."""

    def test_credential_issuer_metadata_returns_correct_json(self, client):
        """Test Credential Issuer Metadata endpoint returns correct JSON."""
        response = client.get("/.well-known/openid-credential-issuer")
        assert response.status_code == 200
        assert response.json == {
            "credential_issuer": "https://example.com",
            "authorization_servers": ["https://authn.example.com"],
            "credential_configurations_supported": {},
        }
