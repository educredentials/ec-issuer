"""End-to-end tests for the OID4VCI flow and metadata."""

import pytest

from tests.e2e.support.admin_client import AdminHttpClient
from tests.e2e.support.browser import Browser
from tests.e2e.support.verifier import Verifier
from tests.e2e.support.wallet import WalletClient


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

        # localhost:8001 is the OID4VCI agent
        assert credential.claims["iss"] == "did:web:localhost%3A8001"


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
