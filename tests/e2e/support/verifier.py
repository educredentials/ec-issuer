"""Verifier client for e2e tests."""

from dataclasses import dataclass

import jwt as jwt_lib
from jwt.api_jwk import PyJWK
import msgspec
from requests import request


@dataclass
class VerificationMethod:
    """A verification method in a DID document."""

    id: str
    type: str
    controller: str
    publicKeyJwk: dict[str, str | list[str]]


@dataclass
class DidDocument:
    """A DID document as defined by W3C DID Core specification."""

    id: str
    verificationMethod: list[VerificationMethod]
    authentication: list[str]
    assertionMethod: list[str]
    context: list[str] | None = None


class Verifier:
    """Verifier client for e2e tests."""

    def verify(self, credential_jwt: str, issuer_did: str) -> bool:
        """Verify a credential JWT by resolving the issuer DID and checking signature.

        Args:
            credential_jwt: The JWT credential to verify.
            issuer_did: The DID of the issuer to resolve and get the public key from.

        Returns:
            True if the credential is valid, False otherwise.

        Raises:
            AssertionError: If the DID cannot be resolved or verification fails.
        """
        # Resolve the DID document to get the public key
        did_document = self.resolve_did_web(issuer_did)

        # Extract the public key from the DID document
        assert len(did_document.verificationMethod) > 0, (
            "No verification methods found in DID document"
        )
        verification_method = did_document.verificationMethod[0]
        public_key_jwk = verification_method.publicKeyJwk
        public_key = PyJWK.from_dict(public_key_jwk)

        # Verify the JWT signature using the public key
        # try:
        _ = jwt_lib.decode(credential_jwt, public_key)
        return True
        # except jwt_lib.InvalidSignatureError:
        #     return False

    def resolve_did_web(self, did_web: str) -> DidDocument:
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
            The resolved DID document.

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

        did_document = msgspec.json.decode(response.content, type=DidDocument)
        assert did_document.id == did_web, (
            f"DID mismatch: expected {did_web}, got {did_document.id}"
        )

        return did_document
