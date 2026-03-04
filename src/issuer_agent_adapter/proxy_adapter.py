"""Proxy adapter for Credential Issuer Metadata."""

from typing import Any

import requests

from ..config import ConfigRepo
from . import (
    IssuerAgentAdapter,
    RequestProtocol,
    RequestsClientProtocol,
    ResponseProtocol,
)


class RequestsResponseWrapper(ResponseProtocol):
    """Wrapper that adapts the requests.Response to our ResponseProtocol."""

    def __init__(self, response: requests.Response) -> None:
        """Initialize the wrapper.

        Args:
            response: The requests.Response object to wrap.
        """
        self._response = response

    @property
    def status_code(self) -> int:
        """The HTTP status code of the response."""
        return self._response.status_code

    @property
    def content(self) -> bytes:
        """The response content as bytes."""
        return self._response.content


class RequestsWrapper(RequestsClientProtocol):
    """Wrapper that adapts the requests module to our RequestsClientProtocol."""

    def get(self, url: str, timeout: int) -> ResponseProtocol:
        """Send a GET request using the requests library.

        Args:
            url: The URL to send the request to.
            timeout: The timeout in seconds.

        Returns:
            A requests.Response object that implements ResponseProtocol.
        """
        return RequestsResponseWrapper(requests.get(url, timeout=timeout))


class ProxyIssuerAgentAdapter(IssuerAgentAdapter):
    """Proxy adapter for Credential Issuer Metadata."""

    def __init__(
        self,
        *,
        config: ConfigRepo,
        requests_client: RequestsClientProtocol = RequestsWrapper(),
    ) -> None:
        """Initialize the proxy adapter.

        Args:
            config: The configuration repository.
            requests_client: The requests client to use.
        """
        self.base_url: str = config.issuer_agent_base_url
        self.requests_client: RequestsClientProtocol = requests_client
        self.timeout: int = 10  # Hardcoded timeout in seconds

    def credential_issuer_metadata(self, request: RequestProtocol) -> ResponseProtocol:
        """Proxy the Credential Issuer Metadata request.

        Args:
            request: The Flask request object.

        Returns:
            A ResponseProtocol object containing the response.
        """
        # Forward the request to the issuer agent
        response = self.requests_client.get(
            f"{self.base_url}/.well-known/openid-credential-issuer",
            timeout=self.timeout,
        )

        # Handle 3xx redirects
        if 300 <= response.status_code < 400:
            # Create a response object for the redirect error
            return RedirectErrorResponse()

        # Return the response as-is (including 4xx and 5xx errors)
        return response


class RedirectErrorResponse(ResponseProtocol):
    """Response object for redirect errors."""

    @property
    def status_code(self) -> int:
        """The HTTP status code."""
        return 400

    @property
    def content(self) -> bytes:
        """The response content as bytes."""
        return b'{"error": "Redirects not supported"}'

    def json(self) -> dict[str, Any]:
        """Parse the response content as JSON."""
        return {"error": "Redirects not supported"}
