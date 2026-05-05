"""End-to-end tests for the OID4VCI flow and metadata."""

import pytest

from tests.e2e.support.admin_client import AdminHttpClient
from tests.e2e.support.browser import Browser
from tests.e2e.support.http_client import Config, HttpClient
from tests.e2e.support.utilities import assert_schema
from tests.e2e.support.verifier import Verifier
from tests.e2e.support.wallet import WalletClient


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
        assert response.headers["content-type"] == "application/json"
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "credential_issuer_metadata")

        # Use wallet_client to verify metadata can be fetched
        metadata = wallet_client.get_issuer_metadata(config.public_url)
        assert metadata.credential_issuer == config.public_url

    def test_did_document_returns_correct_json(self, http_client: HttpClient):
        """Test DID Document endpoint returns correct JSON."""
        response = http_client.get("/.well-known/did.json")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )
        assert response.headers["content-type"] == "application/json"
        body: object = response.json()  # pyright: ignore[reportAny]
        assert_schema(body, "did_document")


@pytest.mark.e2e
class TestOID4VCIFlow:
    def test_get_credential(
        self,
        admin_client: AdminHttpClient,
        wallet_client: WalletClient,
    ):
        """
        Given an offer is created
        And the credential offer is used by a wallet
        When the wallet opens the authorization URL
        And the user completes the authorization
        Then the wallet receives a credential
        And the credential contains the expected issuer DID
        """
        create_offer_response = admin_client.create_offer("award-123")
        offer, metadata, auth_url = wallet_client.use_offer(create_offer_response.uri)

        callback_url = Browser().open(auth_url)
        credential = wallet_client.open_callback_url(callback_url, offer, metadata)

        assert credential.claims["iss"] == "did:web:localhost%3A8000"


@pytest.mark.e2e
class TestVerifyCredential:
    def test_get_verify_credential(
        self,
        admin_client: AdminHttpClient,
        wallet_client: WalletClient,
        verifier: Verifier,
    ):
        """
        Given an offer is created
        And the credential offer is used by a wallet
        When the wallet opens the authorization URL
        And the user completes the authorization
        Then the wallet receives a credential
        And the credential can be verified using the issuer's DID
        """
        create_offer_response = admin_client.create_offer("award-123")
        offer, metadata, auth_url = wallet_client.use_offer(create_offer_response.uri)

        callback_url = Browser().open(auth_url)
        credential = wallet_client.open_callback_url(callback_url, offer, metadata)

        assert verifier.verify(credential.jwt, credential.issuer_did) is True
