"""SSI-Agent Adapter"""

from typing import Protocol, override

import msgspec
import requests

from src.metadata import CredentialIssuerMetadata, IssuerAgentPort

from ..config import ConfigRepo


class SsiAgentHttpResponse(Protocol):
    """
    Interface for HTTP response objects so that we can replace the actual HTTP client.
    """

    @property
    def status_code(self) -> int:
        """The HTTP status code."""
        ...

    @property
    def content(self) -> bytes:
        """The response content as bytes."""
        ...


class SsiAgentHttpClient(Protocol):
    """
    Interface for HTTP client objects so that we can replace the actual HTTP client.
    """

    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Send a GET request.

        Args:
            url: The URL to send the request to.
            timeout: The timeout in seconds.

        Returns:
            A response object.
        """
        ...


class RequestsWrapperResponse(SsiAgentHttpResponse):
    """Wrapper that adapts the requests.Response to our SsiAgentHttpResponse."""

    _response: requests.Response

    def __init__(self, response: requests.Response) -> None:
        """Initialize the wrapper.

        Args:
            response: The requests.Response object to wrap.
        """
        self._response = response

    @property
    @override
    def status_code(self) -> int:
        """The HTTP status code of the response."""
        return self._response.status_code

    @property
    @override
    def content(self) -> bytes:
        """The response content as bytes."""
        return self._response.content


class RequestsWrapper(SsiAgentHttpClient):
    """Wrapper that adapts the requests module to our IssuerAgentHttpClient."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Send a GET request using the requests library.

        Args:
            url: The URL to send the request to.
            timeout: The timeout in seconds.

        Returns:
            A requests.Response object that implements SsiAgentHttpResponse.
        """
        return RequestsWrapperResponse(requests.get(url, timeout=timeout))


class SsiAgentAdapter(IssuerAgentPort):
    """Proxy adapter for Credential Issuer Metadata."""

    def __init__(
        self,
        *,
        config: ConfigRepo,
        requests_client: SsiAgentHttpClient | None = None,
    ) -> None:
        """Initialize the proxy adapter.

        Args:
            config: The configuration repository.
            requests_client: The requests client to use.
        """
        self.base_url: str = config.issuer_agent_base_url
        self.requests_client: SsiAgentHttpClient = requests_client or RequestsWrapper()
        self.timeout: int = 10  # Hardcoded timeout in seconds

    @override
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
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
        if 300 <= int(response.status_code) < 400:
            # Create a response object for the redirect error
            raise MetadataError("Redirects not supported")

        credential_issuer_metadata: CredentialIssuerMetadata = msgspec.json.decode(
            response.content, type=CredentialIssuerMetadata
        )

        # Return the response as-is (including 4xx and 5xx errors)
        return credential_issuer_metadata


class MetadataError(Exception):
    """Exception raised when there is an error in the metadata."""

    pass
