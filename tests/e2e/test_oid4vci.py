"""End-to-end tests for the OID4VCI flow and metadata."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import jsonschema
import jwt
import pytest
from msgspec import json
from requests import request

from tests.e2e.conftest import (
    KEYS_DIR,
    AdminHttpClient,
    Config,
    HttpClient,
    WalletClient,
    assert_schema,
    jsonpath_value,
    load_schema,
)


class Browser:
    """Fake browser to simulate OIDC flow"""

    def open(self, url: str) -> str:
        """Fakes user walking through OIDC flow and returning with an access token"""
        request_args = parse_qs(urlparse(url).query)

        fake_code = "fake_authorization_code"
        issuer_state = request_args["state"][0]
        redirect_uri = request_args["redirect_uri"][0]

        return f"{redirect_uri}?authorization_code={fake_code}&state={issuer_state}"


@dataclass
class CredentialResponse:
    """Domain model representing a credential response."""

    credentials: list[dict[str, str]]


@pytest.mark.e2e
class TestCredentialIssuerMetadataEndpoint:
    """Test the Credential Issuer Metadata endpoint."""

    def test_credential_issuer_metadata_returns_correct_json(
        self, wallet_client: WalletClient, http_client: HttpClient, config: Config
    ):
        """Test Credential Issuer Metadata endpoint returns correct JSON."""
        response = http_client.get("/.well-known/openid-credential-issuer")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "credential_issuer_metadata")

        # Use wallet_client to verify metadata can be fetched
        metadata = wallet_client.get_issuer_metadata(config.public_url)
        assert metadata.credential_issuer == config.public_url


@pytest.mark.e2e
class TestOID4VCIFlow:
    def test_oid4vci_flow(
        self,
        admin_client: AdminHttpClient,
        wallet_client: WalletClient,
    ):
        """
        Given, an offer is created,
        When, the credential offer is used by a wallet,
        Then, the wallet will start the flow and open the authorization in a browser
        And when the user completes the authorization
        The wallet will request the credential using the authorization code
        And the credential will be issued to the wallet
        """
        create_response = admin_client.post(
            "api/v1/offers", json={"achievement_id": "award-123"}
        )
        create_body: object = create_response.json()  # pyright: ignore[reportAny]
        offer_ref: str = jsonpath_value(create_body, "$.uri")  # pyright: ignore[reportAssignmentType]

        offer = wallet_client.get_offer(offer_ref)
        metadata = wallet_client.get_issuer_metadata(offer.credential_issuer)

        assert metadata.authorization_servers is not None
        authorization_server_url = metadata.authorization_servers[0]
        authorization_server_metadata = wallet_client.get_auth_metadata(
            authorization_server_url
        )

        # User is redirected to the authorization server to approve the request
        auth_attributes: dict[str, str] = {
            "response_type": "code",
            "client_id": wallet_client.client_id,
            "redirect_uri": wallet_client.deeplink,
            "scope": "openid%20profile%20email",
            "nonce": "n-0S6_WzA2Mj",
            "state": offer.issuer_state(),
        }
        auth_url = urlparse(authorization_server_metadata.authorization_endpoint)
        auth_url = auth_url._replace(query=urlencode(auth_attributes))

        callback_url = Browser().open(auth_url.geturl())
        authorization_code = parse_qs(urlparse(callback_url).query)[
            "authorization_code"
        ][0]
        access_token = wallet_client.exchange_authorization_code(authorization_code)

        # We only support single credential types
        assert offer.credential_configuration_ids.__len__() == 1

        assert metadata.nonce_endpoint is not None, (
            "nonce_endpoint is not available in metadata, but we require it"
        )
        nonce = wallet_client.get_nonce(metadata.nonce_endpoint)
        proof = wallet_client.proof(metadata.credential_issuer, nonce)

        http_response = request(
            "POST",
            metadata.credential_endpoint,
            json={
                "format": "jwt_vc_json",
                "credential_configuration_id": offer.credential_configuration_ids[0],
                "proof": {
                    "proof_type": "jwt",
                    "jwt": proof,
                },
                "issuer_state": offer.issuer_state(),
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        assert http_response.status_code == 200

        jsonschema.validate(
            json.decode(http_response.text),  # pyright: ignore[reportAny]
            load_schema("credential_response"),
        )
        credential_response = json.decode(http_response.text, type=CredentialResponse)
        assert len(credential_response.credentials) == 1
        credential_jwt = credential_response.credentials[0]["credential"]

        issuer_did = "did:web:localhost%3A8000"
        # TODO: A real world scenario does not have the public key available
        # like this. It must instead resolve the did:web document and extract
        # the public key
        issuer_pubkey = Path(KEYS_DIR / "issuer_eddsa.pub").read_text()
        # Will raise InvalidIssuerError when issuer does not match
        # Will raise InvalidSignatureError when signature is invalid
        _ = jwt.decode(
            credential_jwt, issuer_pubkey, algorithms=["EdDSA"], issuer=issuer_did
        )
