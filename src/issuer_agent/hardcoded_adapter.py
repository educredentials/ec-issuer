"""Hardcoded adapter for Credential Issuer Metadata."""

from typing import override

from src.metadata.metadata import CredentialIssuerMetadata, IssuerAgentPort


class HardcodedIssuerAgentAdapter(IssuerAgentPort):
    """Hardcoded adapter for Credential Issuer Metadata."""

    @override
    def create_offer(self, offer_id: str, achievement_id: str) -> None:
        """No-op stub: offer creation is handled entirely by OfferService for now."""

    @override
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Return hardcoded Credential Issuer Metadata.

        Args:
            request: The Flask request object (unused).

        Returns:
            A ResponseProtocol object containing the hardcoded metadata.
        """
        return HardcodedResponse()


class HardcodedResponse(CredentialIssuerMetadata):
    """Response object for hardcoded metadata."""

    def __init__(self):
        super().__init__(
            credential_issuer="https://issuer.example.com",
            credential_endpoint="https://example.com/credential",
            credential_configurations_supported={},
        )
