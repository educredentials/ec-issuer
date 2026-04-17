"""End-to-end tests for metadata endpoints."""

import pytest

from tests.e2e.conftest import Config, HttpClient, assert_schema, jsonpath_value


@pytest.mark.e2e
class TestCredentialIssuerMetadataEndpoint:
    """Test the Credential Issuer Metadata endpoint."""

    def test_credential_issuer_metadata_returns_correct_json(
        self, e2e_client: HttpClient, config: Config
    ):
        """Test Credential Issuer Metadata endpoint returns correct JSON."""
        response = e2e_client.get("/.well-known/openid-credential-issuer")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "credential_issuer_metadata")
        assert (
            jsonpath_value(body, "$.credential_issuer") == config.public_url
        )
        assert (
            jsonpath_value(body, "$.credential_endpoint")
            == f"{config.public_url}/credential"
        )
        assert (
            jsonpath_value(body, "$.authorization_servers[0]")
            == "https://authn.example.com"
        )
