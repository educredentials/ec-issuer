"""Issuer Agent Adapter module."""

from typing import Any, Protocol


class RequestProtocol:
    """Protocol for Flask request objects."""

    # This is a minimal protocol for Flask requests
    # In practice, Flask's Request class has many more attributes and methods
    pass


class ResponseProtocol(Protocol):
    """Protocol for HTTP response objects."""

    @property
    def status_code(self) -> int:
        """The HTTP status code."""
        ...

    @property
    def content(self) -> bytes:
        """The response content as bytes."""
        ...

    def json(self) -> dict[str, Any]:
        """Parse the response content as JSON.

        Returns:
            The parsed JSON data.
        """
        ...


class RequestsClientProtocol(Protocol):
    """Protocol for HTTP client implementations."""

    def get(self, url: str, timeout: int) -> ResponseProtocol:
        """Send a GET request.

        Args:
            url: The URL to send the request to.
            timeout: The timeout in seconds.

        Returns:
            A response object.
        """
        ...


class IssuerAgentAdapter(Protocol):
    """Protocol for Issuer Agent Adapters."""

    def credential_issuer_metadata(self, request: RequestProtocol) -> ResponseProtocol:
        """Return Credential Issuer Metadata.

        Args:
            request: The Flask request object.

        Returns:
            A ResponseProtocol object containing the response.
        """
        ...
