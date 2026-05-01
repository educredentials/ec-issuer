"""Wallet client for e2e tests."""

import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from urllib.parse import parse_qs, urlencode, urlparse

import jwt as jwt_lib
from jwcrypto import jwk
from msgspec import json as msgspec_json
from requests import request

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata

_TESTS_E2E_DIR = Path(__file__).parent.parent
_KEYS_DIR = _TESTS_E2E_DIR / "keys"


@dataclass
class OpenidConfiguration:
    """Domain model representing an OpenID configuration."""

    authorization_endpoint: str


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


@dataclass
class CredentialResponse:
    """Domain model representing a credential response."""

    credentials: list[dict[str, str]]


@dataclass
class VerifiableCredential:
    """Represents a verifiable credential with its JWT and parsed claims."""

    jwt: str
    claims: dict[str, object]

    @classmethod
    def from_jwt(cls, jwt_str: str) -> "VerifiableCredential":
        """Create a VerifiableCredential from a JWT string without verification."""
        claims: dict[str, object] = jwt_lib.decode(
            jwt_str, options={"verify_signature": False}
        )
        return cls(jwt=jwt_str, claims=claims)

    @property
    def issuer_did(self) -> str:
        """Get the issuer DID from the credential claims."""
        return str(self.claims["iss"])


class WalletClient:
    """Wallet client for e2e tests."""

    client_id: str = "TestWallet"
    deeplink: str = "testwallet://return/"

    def get_offer(self, offer: str) -> Offer:
        """Fetch and parse a credential offer."""
        assert offer.startswith("openid-credential-offer://"), (
            f"Expected offer to start with openid-credential-offer://, got: {offer}"
        )
        credential_offer_uri: str = parse_qs(urlparse(offer).query)[
            "credential_offer_uri"
        ][0]
        assert credential_offer_uri.startswith("http"), (
            f"Expected credential_offer_uri to be HTTP, got: {credential_offer_uri}"
        )

        response = request("GET", credential_offer_uri)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )
        return msgspec_json.decode(response.text, type=Offer)

    def get_issuer_metadata(self, issuer_url: str) -> CredentialIssuerMetadata:
        """Fetch credential issuer metadata."""
        response = request(
            "GET", f"{issuer_url}/.well-known/openid-credential-issuer"
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )

        metadata = msgspec_json.decode(response.text, type=CredentialIssuerMetadata)

        return metadata

    def get_nonce(self, nonce_endpoint: str) -> str:
        """Return the c_nonce for the credential offer."""

        response = request(
            "POST",
            nonce_endpoint,
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}, {response.text[:200]}"
        )

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

    def use_offer(self, offer_uri: str) -> tuple[Offer, CredentialIssuerMetadata, str]:
        """Fetch and parse a credential offer, get its metadata, and return auth URL.

        Args:
            offer_uri: The URI of the credential offer.

        Returns:
            A tuple of (offer, metadata, auth_url).
        """
        offer = self.get_offer(offer_uri)
        metadata = self.get_issuer_metadata(offer.credential_issuer)

        assert metadata.authorization_servers is not None, (
            "authorization_servers is None in metadata"
        )

        auth_metadata = self.get_auth_metadata(metadata.authorization_servers[0])
        auth_attributes: dict[str, str] = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.deeplink,
            "scope": "openid%20profile%20email",
            "nonce": "n-0S6_WzA2Mj",
            "state": offer.issuer_state(),
        }
        auth_url = urlparse(auth_metadata.authorization_endpoint)
        auth_url = auth_url._replace(query=urlencode(auth_attributes)).geturl()

        return offer, metadata, auth_url

    def open_callback_url(
        self,
        callback_url: str,
        offer: Offer,
        metadata: CredentialIssuerMetadata,
    ) -> VerifiableCredential:
        """Handle callback URL: extract code, exchange for token, request credential.

        Args:
            callback_url: The callback URL from the OIDC flow.
            offer: The credential offer.
            metadata: The credential issuer metadata.

        Returns:
            The verifiable credential (unverified, parsed claims).
        """
        # Parse callback URL for authorization code
        callback_query = parse_qs(urlparse(callback_url).query)
        assert "authorization_code" in callback_query, (
            f"authorization_code not found in callback URL: {callback_url}"
        )
        authorization_code = callback_query["authorization_code"][0]

        # Exchange authorization code for access token
        access_token = self.exchange_authorization_code(authorization_code)

        # Request credential
        credential_response = self.request_credential(metadata, offer, access_token)
        assert len(credential_response.credentials) == 1, (
            f"Expected 1 credential, got {len(credential_response.credentials)}"
        )
        credential_jwt = credential_response.credentials[0]["credential"]

        return VerifiableCredential.from_jwt(credential_jwt)

    def request_credential(
        self,
        metadata: CredentialIssuerMetadata,
        offer: Offer,
        access_token: str,
    ) -> CredentialResponse:
        """Request a credential from the issuer.

        Args:
            metadata: The credential issuer metadata.
            offer: The credential offer.
            access_token: The access token for authorization.

        Returns:
            The credential response.
        """
        assert metadata.nonce_endpoint is not None, (
            "nonce_endpoint is not available in metadata, but we require it"
        )
        nonce = self.get_nonce(metadata.nonce_endpoint)
        proof = self.proof(metadata.credential_issuer, nonce)

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
        assert http_response.status_code == 200, (
            f"Expected 200, got {http_response.status_code}, {http_response.text[:200]}"
        )
        return msgspec_json.decode(http_response.text, type=CredentialResponse)

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

        proof = jwt_lib.encode(
            payload=payload, key=self._private_key(), algorithm="EdDSA", headers=header
        )

        # Assert we comply with above linked specification.
        check = jwt_lib.decode_complete(
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
        }, f"Proof JWT header mismatch: {check['header']}"
        assert check["payload"]["aud"] is not None, "Proof JWT missing aud claim"
        assert check["payload"]["iat"] is not None, "Proof JWT missing iat claim"

        return proof

    def _private_key(self) -> str:
        """Return the EdDSA (Ed25519) private key of the wallet."""
        return Path(_KEYS_DIR / "wallet_holder_eddsa.priv").read_text()

    def _public_key(self) -> str:
        """Return the EdDSA (Ed25519) public key of the wallet."""
        return Path(_KEYS_DIR / "wallet_holder_eddsa.pub").read_text()

    def public_jwk(self) -> str:
        """Return the JWK of the wallet."""
        jwk_key = jwk.JWK.from_pem(data=self._private_key().encode(), password=None)
        return jwk_key.export()

    def did(self) -> str:
        """Return the DID of the wallet."""
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
