from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jsonschema
import jwt
import pytest
from jsonpath_ng import (  # pyright: ignore[reportMissingTypeStubs]
    parse as jsonpath_parse,  # pyright: ignore[reportUnknownVariableType]
)
from jwcrypto import jwk
from msgspec import json as msgspec_json
from requests import request

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata

_SCHEMAS_DIR = Path(__file__).parent / "schemas"
KEYS_DIR = Path(__file__).parent / "keys"


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
    _default_headers: dict[str, str] = {}

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


@dataclass
class CredentialInfo:
    """Credential information from cli-vc-wallet."""

    issuer: str
    subject: str
    verifiable_credential: object | None = None
    header: dict[str, object] | None = None


@dataclass
class VerificationResult:
    """Verification result from cli-vc-wallet.

    This is the full structure returned by the cli-vc-wallet verify command.
    """

    valid: bool
    credential_info: CredentialInfo
    errors: list[Exception]

    @staticmethod
    def default() -> "VerificationResult":
        return VerificationResult(
            valid=False,
            credential_info=CredentialInfo(issuer="", subject=""),
            errors=[],
        )


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
        response = request("GET", f"{issuer_url}/.well-known/openid-credential-issuer")
        assert response.status_code == 200
        metadata = msgspec_json.decode(response.text, type=CredentialIssuerMetadata)

        return metadata

    def get_nonce(self, nonce_endpoint: str) -> str:
        """Return the c_nonce for the credential offer."""

        response = request(
            "POST",
            nonce_endpoint,
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200

        data = msgspec_json.decode(response.text, type=dict[str, str])
        assert "c_nonce" in data, "c_nonce not found in response"
        return data["c_nonce"]

    def get_auth_metadata(self, auth_server_url: str) -> OpenidConfiguration:
        """Fetch authorization server metadata."""
        return OpenidConfiguration(
            authorization_endpoint=f"{auth_server_url}/authorize",
        )

    def exchange_authorization_code(self, _authorization_code: str) -> str:
        """Exchange authorization code for access token."""
        return "fake_access_token"

    def proof(self, credential_issuer: str, nonce: str) -> str:
        """Generate a proof JWT."""

        # TODO: we now support only jwk in the header, not kid. Do we want to be
        # able to select one of both?
        # TODO: we build a JWT, regardless of whether the issuer-metadata has
        # this as supported option.
        #
        # See https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0-ID2.html#jwt-proof-type
        header: dict[str, str] = {
            "typ": "openid4vci-proof+jwt",
            "jwk": self.public_jwk(),
        }

        # TODO: "iss": This claim MUST be omitted if the access token
        # authorizing the issuance call was obtained from a Pre-Authorized Code
        # Flow through anonymous access to the token endpoint.
        payload: dict[str, str | int] = {
            "iss": self.client_id,
            "aud": credential_issuer,
            "iat": int(datetime.now().timestamp()),
            "nonce": nonce,
        }

        proof = jwt.encode(
            payload=payload, key=self._private_key(), algorithm="EdDSA", headers=header
        )

        # Assert we comply with above linked specification.
        check = jwt.decode_complete(
            proof,
            key=self._public_key(),
            algorithms=["EdDSA"],
            audience=credential_issuer,
            issuer=self.client_id,
        )
        assert check["header"] == {
            "alg": "EdDSA",
            "typ": "openid4vci-proof+jwt",
            "jwk": self.public_jwk(),
        }
        assert check["payload"]["aud"] is not None
        assert check["payload"]["iat"] is not None

        return proof

    def _private_key(self) -> str:
        """Return the EdDSA (Ed25519) private key of the wallet"""
        return Path(KEYS_DIR / "wallet_holder_eddsa.priv").read_text()

    def _public_key(self) -> str:
        """Return the EdDSA (Ed25519) public key of the wallet"""
        return Path(KEYS_DIR / "wallet_holder_eddsa.pub").read_text()

    def public_jwk(self) -> str:
        """Return the JWK of the wallet"""
        jwk_key = jwk.JWK.from_pem(data=self._private_key().encode(), password=None)
        return jwk_key.export()

    def did(self) -> str:
        """Return the DID of the wallet"""
        # We use a did:jwk to be explicit. A did:key could be used too, but
        # is more ambiguous.
        # See https://github.com/quartzjer/did-jwk/blob/main/spec.md
        # Generate or load a JWK
        jwk = self.public_jwk()
        # Serialize it into a UTF-8 string
        serialized = jwk.encode()
        # Encode that string using base64url. Remove padding. Stupid Python
        encoded = base64.urlsafe_b64encode(serialized).rstrip(b"=")
        # Attach the prefix did:jwk: Decode as UTF-8
        return f"did:jwk:{encoded.decode()}"


class Verifier:
    """Verifier client for e2e tests."""

    def verify(self, credential_jwt: str, issuer_public_key: str) -> VerificationResult:
        verification_result = VerificationResult.default()
        verification_result.credential_info.header = jwt.get_unverified_header(
            credential_jwt
        )

        try:
            result: dict[str, str] = jwt.decode(
                credential_jwt, issuer_public_key, algorithms=["EdDSA"]
            )
            verification_result.valid = True
            verification_result.credential_info = CredentialInfo(
                issuer=result["iss"], subject=result["sub"]
            )
        except jwt.InvalidSignatureError as e:
            verification_result.valid = False
            verification_result.errors.append(e)

        return verification_result

    def is_for_holder(self, _credential_jwt: str, _holder_did: str) -> bool:
        # # It was signed for the wallet holder
        # assert credential["sub"] is not None
        # assert credential["sub"] == credential["credentialSubject"]["id"]
        # assert credential["sub"] == wallet_client.did()
        return True

    def resolve_did_web(self, did_web: str) -> dict[str, object]:
        """Resolve a DID Web document according to the W3C specification.

        The following steps are executed:
        1. Replace ":" with "/" in the method specific identifier.
        2. If the domain contains a port, percent decode the colon.
        3. Generate an HTTPS URL by prepending https://.
        4. If no path is specified, append /.well-known.
        5. Append /did.json to complete the URL.
        6. Perform an HTTP GET request.
        7. Verify that the ID of the resolved DID document matches the Web DID
        being resolved.

        Args:
            did_web: The DID Web to resolve, e.g. "did:web:example.com:issuers:876543".

        Returns:
            The resolved DID document as a dictionary.

        Raises:
            AssertionError: If the DID is not a valid did:web DID.
            AssertionError: If the resolved DID document ID doesn't match the input DID.
        """
        # Validate input
        assert did_web.startswith("did:web:"), f"Expected did:web: DID, got: {did_web}"

        # Step 1: Remove "did:web:" prefix
        method_specific_id = did_web[8:]  # Remove "did:web:"

        # Step 2: Replace ":" with "/" in the method specific identifier
        path = method_specific_id.replace(":", "/")
        # Replace %3a with the actual colon character for ports separator
        path = path.replace("%3A", ":")

        # Step 3: Generate HTTPS URL by prepending https://
        # Non-standard: make an exception for localhost, allow that over http
        if path.startswith("localhost"):
            url = f"http://{path}"
        else:
            url = f"https://{path}"

        # Step 4: If no path has been specified, append /.well-known
        # Check if the URL already has a path component
        if "/" not in url[8:]:  # Check after "https://"
            url = f"{url}/.well-known"

        # Step 5: Append /did.json
        url = f"{url}/did.json"

        # Step 6: Perform HTTP GET request
        response = request("GET", url, timeout=10)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )

        # Parse the response
        did_document: dict[str, object] = response.json()  # pyright: ignore[reportAny]

        # Step 7: Verify the ID matches
        assert did_document.get("id") == did_web, (
            f"DID mismatch: expected {did_web}, got {did_document.get('id')}"
        )

        return did_document


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
