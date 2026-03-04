"""Hardcoded adapter for Credential Issuer Metadata."""

from typing import Any

from . import IssuerAgentAdapter, RequestProtocol, ResponseProtocol


class HardcodedIssuerAgentAdapter(IssuerAgentAdapter):
    """Hardcoded adapter for Credential Issuer Metadata."""

    def credential_issuer_metadata(self, request: RequestProtocol) -> ResponseProtocol:
        """Return hardcoded Credential Issuer Metadata.

        Args:
            request: The Flask request object (unused).

        Returns:
            A ResponseProtocol object containing the hardcoded metadata.
        """
        return HardcodedResponse()


class HardcodedResponse(ResponseProtocol):
    """Response object for hardcoded metadata."""

    @property
    def status_code(self) -> int:
        """The HTTP status code."""
        return 200

    @property
    def content(self) -> bytes:
        """The response content as bytes."""
        return (
            b'{"credential_issuer": "https://example.com", '
            b'"authorization_servers": ["https://authn.example.com"], '
            b'"credential_configurations_supported": {}}'
        )

    def json(self) -> dict[str, Any]:
        """Parse the response content as JSON."""
        return {
            "credential_issuer": "https://example.com",
            "authorization_servers": ["https://authn.example.com"],
            "credential_configurations_supported": {},
        }
