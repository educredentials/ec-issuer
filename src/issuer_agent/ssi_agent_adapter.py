"""SSI-Agent Adapter for offer and credential operations."""

from typing import Protocol, override

import msgspec
import requests

from src.config.config_port import ConfigRepoPort
from src.credentials.credential import CredentialResponse
from src.issuer_agent.issuer_agent_port import IssuerAgentError
from src.issuer_agent.issuer_agent_port import IssuerAgentPort
from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata


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

    def post(
        self,
        url: str,
        data: bytes,
        headers: dict[str, str],
        timeout: int,
    ) -> SsiAgentHttpResponse:
        """Send a POST request.

        Args:
            url: The URL to send the request to.
            data: The request body as bytes.
            headers: The request headers.
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

    @override
    def post(
        self,
        url: str,
        data: bytes,
        headers: dict[str, str],
        timeout: int,
    ) -> SsiAgentHttpResponse:
        """Send a POST request using the requests library.

        Args:
            url: The URL to send the request to.
            data: The request body as bytes.
            headers: The request headers.
            timeout: The timeout in seconds.

        Returns:
            A requests.Response object that implements SsiAgentHttpResponse.
        """
        return RequestsWrapperResponse(
            requests.post(url, data=data, headers=headers, timeout=timeout)
        )


class SsiAgentAdapter(IssuerAgentPort):
    """Proxy adapter for Credential Issuer Metadata."""

    def __init__(
        self,
        *,
        config: ConfigRepoPort,
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
    def create_offer(self, offer_id: str, achievement_id: str) -> None:
        """Stub — will delegate to the SSI agent in a future iteration."""

    @override
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Not supported - use SsiAgentMetadataAdapter for metadata."""
        raise NotImplementedError("Use SsiAgentMetadataAdapter for metadata")

    @override
    def credential_request(
        self,
        format: str,
        credential_configuration_id: str,
        proof: dict[str, object],
        issuer_state: str,
        access_token: str,
    ) -> CredentialResponse:
        """Proxy the credential request to the SSI agent.

        Args:
            format: The credential format.
            credential_configuration_id: The credential configuration identifier.
            proof: The proof object containing proof_type and jwt.
            issuer_state: The issuer state from the offer.
            access_token: The access token for authorization.

        Returns:
            CredentialResponse containing the issued credential(s).

        Raises:
            IssuerAgentError: When the upstream request fails.
        """
        request_body = {
            "format": format,
            "credential_configuration_id": credential_configuration_id,
            "proof": proof,
            "issuer_state": issuer_state,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        # Forward the request to the issuer agent
        response = self.requests_client.post(
            f"{self.base_url}/credential",
            data=msgspec.json.encode(request_body),
            headers=headers,
            timeout=self.timeout,
        )

        # Handle HTTP errors from upstream
        if 400 <= int(response.status_code) < 600:
            raise IssuerAgentError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        credential_response: CredentialResponse = msgspec.json.decode(
            response.content, type=CredentialResponse
        )

        return credential_response

    @override
    def request_nonce(self) -> dict[str, str]:
        """Request a nonce from the issuer agent.

        Returns:
            A dictionary containing the c_nonce.

        Raises:
            IssuerAgentError: When the upstream request fails.
        """
        response = self.requests_client.post(
            f"{self.base_url}/nonce",
            data=b"",
            headers={},
            timeout=self.timeout,
        )

        # Handle HTTP errors from upstream
        if 400 <= int(response.status_code) < 600:
            raise IssuerAgentError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        return msgspec.json.decode(response.content, type=dict[str, str])
