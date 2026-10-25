"""End-to-end tests for the OID4VCI flow and metadata."""

import pytest

from tests.e2e.support.admin_client import AdminHttpClient
from tests.e2e.support.browser import Browser
from tests.e2e.support.verifier import Verifier
from tests.e2e.support.wallet import WalletClient


class TestOID4VCIFlow:
    @pytest.mark.parametrize("credential_type", ["ob3", "edc"])
    def test_get_credential_credential_type(
        self,
        admin_client: AdminHttpClient,
        wallet_client: WalletClient,
        credential_type: str,
    ):
        """
        Given an offer is created with a specific credential type
        And the credential offer is used by a wallet
        When the wallet opens the authorization URL
        And the user completes the authorization
        Then the wallet receives a credential
        And the credential contains the expected issuer DID
        """
        create_offer_response = admin_client.create_offer(
            "award-123", credential_type=credential_type
        )
        offer, metadata, auth_url = wallet_client.use_offer(create_offer_response.uri)

        callback_url = Browser().open(auth_url)
        credential = wallet_client.open_callback_url(callback_url, offer, metadata)

        # OB3 uses mock-ssi-agent on port 8001, EDC uses mock on port 8005
        port = 8005 if credential_type == "edc" else 8001
        assert credential.claims["iss"] == f"did:web:localhost%3A{port}"

    @pytest.mark.parametrize("credential_type", ["ob3", "edc"])
    def test_get_credential_type(
        self,
        admin_client: AdminHttpClient,
        wallet_client: WalletClient,
        credential_type: str,
    ):
        """
        Given an offer is created
        And the credential offer is used by a wallet
        Then the issued credential contains the expected credential type.
        """
        create_offer_response = admin_client.create_offer(
            "award-123", credential_type=credential_type
        )
        offer, metadata, auth_url = wallet_client.use_offer(create_offer_response.uri)

        callback_url = Browser().open(auth_url)
        credential = wallet_client.open_callback_url(
            callback_url, offer, metadata
        )

        credential_types = credential.claims["type"]
        assert isinstance(credential_types, list), "Credential type must be a list"
        if credential_type == "ob3":
            assert "OpenBadgeCredential" in credential_types
        else:
            assert "EuropeanDigitalCredential" in credential_types


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
