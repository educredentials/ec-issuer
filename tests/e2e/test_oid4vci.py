"""End-to-end tests for the OID4VCI flow. AKA import in wallet"""

from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse

import jsonschema
import pytest
from msgspec import json
from requests import request

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from tests.e2e.conftest import HttpClient, jsonpath_value, load_schema


@dataclass
class OpenidConfiguration:
    """Domain model representing an OpenID configuration."""

    authorization_endpoint: str


@dataclass
class CredentialResponse:
    """Domain model representing a credential response."""

    credentials: list[dict[str, str]]


@dataclass
class Offer:
    """Domain model representing a credential offer."""

    credential_issuer: str
    credential_configuration_ids: list[str]
    grants: dict[str, dict[str, str]]

    def issuer_state(self) -> str:
        assert "authorization_code" in self.grants
        assert "issuer_state" in self.grants["authorization_code"]
        return self.grants["authorization_code"]["issuer_state"]


class Browser:
    """Fake browser to simulate OIDC flow"""

    def open(self, url: str) -> str:
        """Fakes user walking through OIDC flow and returning with an access token"""
        request_args = parse_qs(urlparse(url).query)

        fake_code = "fake_authorization_code"
        issuer_state = request_args["state"][0]
        redirect_uri = request_args["redirect_uri"][0]

        return f"{redirect_uri}?authorization_code={fake_code}&state={issuer_state}"


class Wallet:
    client_id: str = "TestWallet"
    deeplink: str = "testwallet://return/"

    def __init__(self) -> None:
        pass

    def get_offer(self, offer: str) -> Offer:
        assert offer.startswith("openid-credential-offer://")
        credential_offer_uri: str = parse_qs(urlparse(offer).query)[
            "credential_offer_uri"
        ][0]
        assert credential_offer_uri.startswith("http")

        response = request("GET", credential_offer_uri)
        assert response.status_code == 200
        return json.decode(response.text, type=Offer)

    def get_issuer_metadata(self, issuer_url: str) -> CredentialIssuerMetadata:
        response = request("GET", f"{issuer_url}/.well-known/openid-credential-issuer")
        assert response.status_code == 200
        return json.decode(response.text, type=CredentialIssuerMetadata)

    def get_auth_metadata(self, auth_server_url: str) -> OpenidConfiguration:
        # We don't want to test auth server, so instead of fetching, we return
        # hardcoded values.
        # Below is what an actual request would be done with:
        # resp = request("GET", f"{auth_server_url}/.well-known/openid-configuration")
        # assert resp.status_code == 200
        return OpenidConfiguration(
            authorization_endpoint=f"{auth_server_url}/authorize",
        )

    def open_deeplink(self, deeplink: str) -> str:
        return deeplink

    def exchange_authorization_code(self, _authorization_code: str) -> str:
        # TODO: Replace with a JWT that holds the expected claims
        return "fake_access_token"

    def proof(self) -> str:
        # TODO: build a JWT that:
        # - includes the c_nonce,
        # - signed by us, using a did and a key
        # - exp and iat dates to now
        # - sub is set to issuers url
        return "eyJ0eXAiOiJvcGVuaWQ0dmNpLXByb29mK2p3dCIsImFsZyI6IkVTMjU2IiwiandrIjp7ImFsZyI6IkVTMjU2Iiwia3R5IjoiRUMiLCJjcnYiOiJQLTI1NiIsIngiOiJPWkJmUU9kVkhOYXYwRTZWdF8tRFV4VFdEd3JrdkMtenJYYWNoVUtDSlowIiwieSI6ImdrTGotR2d6eV90VzhHSWptVEpsTWV1ZTdQYVd4Nk16b1BrLV9OT0g4YncifX0.eyJpc3MiOiJkaWQ6a2V5Ono2TWtxWmRUMUdkRTl2U0ZjQnJXUEZmUlhCemdSNmJ3dW9td3lNZHFxbWoyeENjaiIsImF1ZCI6Imh0dHBzOi8vaXNzdWVyLmV4YW1wbGUuY29tIiwiaWF0IjoxNzc2NDMzNzAyLCJleHAiOjE3NzY0MzczMDIsIm5vbmNlIjpudWxsfQ.k4oYGz5Jak4am0zgq3ciUF_TqYQAH5Vbs4jdd-G_b06e-bwcHhjd4bN0qSxi5onQtS3dB7Ka064Cb2QiECaUdg"  # noqa: E501 Because there's no clean way to hardcode a long JWT string in python


@pytest.mark.e2e
class TestOID4VCIFlow:
    def test_oid4vci_flow(self, e2e_client: HttpClient):
        """
        Given, an offer is created,
        When, the credential offer is used by a wallet,
        Then, the wallet will start the flow and open the authorization in a browser
        And when the user completes the authorization
        The wallet will request the credential using the authorization code
        And the credential will be issued to the wallet
        """
        wallet = Wallet()
        admin_client = e2e_client

        create_response = admin_client.post(
            "api/v1/offers",
            json={"achievement_id": "award-123"},
            headers={"Authorization": "Bearer test-token"},
        )
        create_body: object = create_response.json()  # pyright: ignore[reportAny]
        offer_ref: str = jsonpath_value(create_body, "$.uri")  # pyright: ignore[reportAssignmentType]

        # Dereference the offer
        offer = wallet.get_offer(offer_ref)
        # Fetch credential issuer metada from well known
        metadata = wallet.get_issuer_metadata(offer.credential_issuer)

        # Grab the authorization server from the metadata
        assert metadata.authorization_servers is not None
        authorization_server_url = metadata.authorization_servers[0]

        # Fetch authorization server metadata
        authorization_server_metadata = wallet.get_auth_metadata(
            authorization_server_url
        )

        # User would be redirected to the authorization server to approve the request
        auth_attributes: dict[str, str] = {
            "response_type": "code",
            "client_id": wallet.client_id,
            "redirect_uri": wallet.deeplink,
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
        # Exchange the access token for an author
        access_token = wallet.exchange_authorization_code(authorization_code)

        # We only support single credential types for now, otherwise we'd have to
        # loop through each credential configuration id and make a separate request.
        assert offer.credential_configuration_ids.__len__() == 1

        http_response = request(
            "POST",
            metadata.credential_endpoint,
            json={
                "format": "jwt_vc_json",
                "credential_configuration_id": offer.credential_configuration_ids[0],
                "proof": {
                    "proof_type": "jwt",
                    "jwt": wallet.proof(),
                },
                "issuer_state": offer.issuer_state(),
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        assert http_response.status_code == 200
        # Decode
        credential_response = json.decode(
            http_response.text, type=CredentialResponse
        )

        jsonschema.validate(
            http_response.json(), load_schema("credential_response")  # pyright: ignore[reportAny]
        )
        assert isinstance(credential_response.credentials, list)
        assert len(credential_response.credentials) == 1
        credential_jwt = credential_response.credentials[0]["credential"]

        # TODO: verify and unpack the credential JWT
        # assert valid,
        # assert signed by the issuer,
        # assert claims.vc is a full blown OBv3 Credential
        assert credential_jwt.startswith("ey")
