from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jsonschema
import pytest
from jsonpath_ng import (  # pyright: ignore[reportMissingTypeStubs]
    parse as jsonpath_parse,  # pyright: ignore[reportUnknownVariableType]
)
from msgspec import json as msgspec_json
from requests import request

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata

_SCHEMAS_DIR = Path(__file__).parent / "schemas"


def load_schema(schema_name: str) -> dict[str, object]:
    """Load a JSON schema file from the schemas directory.

    Args:
        schema_name: Filename without extension, e.g. "credential_offer".

    Returns:
        The parsed schema as a dictionary.
    """
    return json.loads(  # pyright: ignore[reportAny]
        (_SCHEMAS_DIR / f"{schema_name}.json").read_text()
    )


def assert_schema(data: object, schema_name: str) -> None:
    """Validate data against a JSON schema file in the schemas directory.

    Args:
        data: The parsed JSON data to validate.
        schema_name: Filename without extension, e.g. "credential_offer".

    Raises:
        jsonschema.ValidationError: When data does not match the schema.
    """
    jsonschema.validate(data, load_schema(schema_name))


def jsonpath_value(data: object, expression: str) -> object:
    """Extract a single value from data using a JSONPath expression.

    Args:
        data: The parsed JSON data to search.
        expression: A JSONPath expression, e.g. "$.grants.issuer_state".

    Returns:
        The first matched value.

    Raises:
        IndexError: When the expression matches nothing.
    """
    matches = jsonpath_parse(expression).find(data)  # pyright: ignore[reportUnknownMemberType]
    return matches[0].value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]


class Config:
    """E2E test configuration loaded from environment variables."""

    public_url: str = os.environ["PUBLIC_URL"]


class HttpClient:
    """Thin HTTP client for e2e tests."""

    _service_url: str
    _default_headers: dict[str, str]

    def __init__(self, config: Config):
        """Initialise with service base URL from config.

        Args:
            config: Test configuration.
        """
        self._service_url = config.public_url
        self._default_headers = {}

    def get(self, path: str, headers: dict[str, str] | None = None):
        """Send a GET request to the service.

        Args:
            path: URL path relative to the service base URL.
            headers: Optional HTTP headers.
        """
        return self._request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ):
        """Send a POST request to the service.

        Args:
            path: URL path relative to the service base URL.
            json: Request body as a dict, serialised to JSON.
            headers: Optional HTTP headers.
        """
        return self._request("POST", path, json=json, headers=headers)

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ):
        url = f"{self._service_url}/{path}"
        combined_headers = {**self._default_headers, **(headers or {})}
        return request(method, url, json=json, headers=combined_headers)


class AdminHttpClient(HttpClient):
    """HTTP client for e2e tests that adds admin authentication headers."""

    def __init__(self, config: Config):
        """Initialise with service base URL from config and admin headers.

        Args:
            config: Test configuration.
        """
        super().__init__(config)
        self._default_headers: dict[str, str] = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }


@dataclass
class OpenidConfiguration:
    """Domain model representing an OpenID configuration."""

    authorization_endpoint: str


class WalletClient:
    """Wallet client for e2e tests."""

    client_id: str = "TestWallet"
    deeplink: str = "testwallet://return/"

    def get_offer(self, offer: str) -> "Offer":
        """Fetch and parse a credential offer."""
        assert offer.startswith("openid-credential-offer://")
        credential_offer_uri: str = parse_qs(urlparse(offer).query)[
            "credential_offer_uri"
        ][0]
        assert credential_offer_uri.startswith("http")

        response = request("GET", credential_offer_uri)
        assert response.status_code == 200
        return msgspec_json.decode(response.text, type=Offer)

    def get_issuer_metadata(self, issuer_url: str) -> CredentialIssuerMetadata:
        """Fetch credential issuer metadata."""
        response = request(
            "GET", f"{issuer_url}/.well-known/openid-credential-issuer"
        )
        assert response.status_code == 200
        return msgspec_json.decode(response.text, type=CredentialIssuerMetadata)

    def get_auth_metadata(self, auth_server_url: str) -> OpenidConfiguration:
        """Fetch authorization server metadata."""
        return OpenidConfiguration(
            authorization_endpoint=f"{auth_server_url}/authorize",
        )

    def exchange_authorization_code(self, _authorization_code: str) -> str:
        """Exchange authorization code for access token."""
        return "fake_access_token"

    def proof(self) -> str:
        """Generate a proof JWT."""
        return (
            "eyJ0eXAiOiJvcGVuaWQ0dmNpLXByb29mK2p3dCIsImFsZyI6IkVTMjU2IiwiandrIjp7ImFsZyI6IkVTMjU2Iiwia3R5Ijp7ImFsZyI6IkVDIiwiY3J2IjoiUC0yNTYiLCJ4IjoiRUMifX0sIngiOiJPWkJmUU9kVkhOYXYwRTZWdF8tRFV4VFdEd3JrdkMtenJYYWNoVUtDSlowIiwieSI6ImdrTGotR2d6eV90VzhHSWptVEpsTWV1ZTdQYVd4Nk16b1BrLV9OT0g4YncifX0.eyeJpc3MiOiJkaWQ6a2V5Ono2TWtxWmRUMUdkRTl2U0ZjQnJXUEZmUlhCemdSNmJ3dW9td3lNZHFxbWoyeENnaiIsImF1ZCI6Imh0dHBzOi8vaXNzdWVyLmV4YW1wbGUuY29tIiwiaWF0IjoxNzc2NDMzNzAyLCJleHAiOjE3NzY0MzczMDIsIm5vbmNlIjpudWxsfQ.k4oYGz5Jak4am0zgq3ciUF_TqYQAH5Vbs4jdd-G_b06e-bwcHhjd4bN0qSxi5onQtS3dB7Ka064Cb2QiECaUdg"
        )


@dataclass
class Offer:
    """Domain model representing a credential offer."""

    credential_issuer: str
    credential_configuration_ids: list[str]
    grants: dict[str, dict[str, str]]

    def issuer_state(self) -> str:
        """Get the issuer state from the offer."""
        assert "authorization_code" in self.grants
        assert "issuer_state" in self.grants["authorization_code"]
        return self.grants["authorization_code"]["issuer_state"]


@pytest.fixture(scope="session")
def config() -> Config:
    """Provide test configuration."""
    return Config()


@pytest.fixture(scope="session")
def http_client(config: Config) -> HttpClient:
    """Provide a generic HTTP client pointed at the service under test."""
    return HttpClient(config)


@pytest.fixture(scope="session")
def admin_client(config: Config) -> AdminHttpClient:
    """Provide an admin HTTP client with auth headers."""
    return AdminHttpClient(config)


@pytest.fixture(scope="session")
def wallet_client() -> WalletClient:
    """Provide a wallet client for e2e tests."""
    return WalletClient()
