"""SSI-Agent adapter for the metadata repository."""

from typing import Protocol, override

import msgspec
import requests

from src.config.config_port import ConfigRepoPort
from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import (
    MetadataNotFoundError,
    MetadataRepositoryPort,
    MetadataSerializationError,
)


class SsiAgentMetadataHttpResponse(Protocol):
    """Interface for HTTP response objects for metadata requests."""

    @property
    def status_code(self) -> int:
        """The HTTP status code."""
        ...

    @property
    def content(self) -> bytes:
        """The response content as bytes."""
        ...


class SsiAgentMetadataHttpClient(Protocol):
    """Interface for HTTP client objects for metadata requests."""

    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Send a GET request.

        Args:
            url: The URL to send the request to.
            timeout: The timeout in seconds.

        Returns:
            A response object.
        """
        ...


class RequestsWrapperResponse(SsiAgentMetadataHttpResponse):
    """Wrapper that adapts the requests.Response to our SsiAgentMetadataHttpResponse."""

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


class RequestsWrapper(SsiAgentMetadataHttpClient):
    """Wrapper that adapts the requests module to our SsiAgentMetadataHttpClient."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Send a GET request using the requests library.

        Args:
            url: The URL to send the request to.
            timeout: The timeout in seconds.

        Returns:
            A requests.Response object that implements SsiAgentMetadataHttpResponse.
        """
        return RequestsWrapperResponse(requests.get(url, timeout=timeout))


class SsiAgentMetadataAdapter(MetadataRepositoryPort):
    """Adapter that fetches metadata from an SSI-Agent."""

    _base_url: str
    _public_url: str
    _requests_client: SsiAgentMetadataHttpClient
    _timeout: int

    def __init__(
        self,
        *,
        config: ConfigRepoPort,
        requests_client: SsiAgentMetadataHttpClient | None = None,
    ) -> None:
        """Initialize the SSI-Agent metadata repository.

        Args:
            config: The configuration repository.
            requests_client: The requests client to use.
        """
        self._base_url = config.ssi_agent_url
        self._public_url = config.public_url
        self._requests_client = requests_client or RequestsWrapper()
        self._timeout = 10  # Hardcoded timeout in seconds

    @override
    def store(self, metadata: CredentialIssuerMetadata) -> None:
        """Store is not supported for SSI-Agent metadata repository.

        Args:
            metadata: The metadata to store (not stored, as this is read-only).

        Raises:
            NotImplementedError: Always, as this adapter is read-only.
        """
        raise NotImplementedError(
            "SsiAgentMetadataRepository is read-only and does not support store"
        )

    @override
    def get(self) -> CredentialIssuerMetadata:
        """Retrieve metadata from the SSI-Agent.

        Returns:
            The CredentialIssuerMetadata from the upstream agent.

        Raises:
            MetadataNotFoundError: When redirects are encountered or request fails.
            MetadataSerializationError: When metadata cannot be deserialized.
        """
        # Forward the request to the issuer agent
        response = self._requests_client.get(
            f"{self._base_url}/.well-known/openid-credential-issuer",
            timeout=self._timeout,
        )

        # Handle 3xx redirects
        if 300 <= int(response.status_code) < 400:
            raise MetadataNotFoundError("Redirects not supported")

        # Handle other errors
        if response.status_code != 200:
            raise MetadataNotFoundError(
                f"Failed to fetch metadata: HTTP {response.status_code}"
            )

        try:
            metadata = msgspec.json.decode(
                response.content, type=CredentialIssuerMetadata
            )
        except msgspec.DecodeError as e:
            raise MetadataSerializationError(
                f"Failed to deserialize metadata from SSI-Agent: {e}"
            ) from e

        return CredentialIssuerMetadata(
            credential_issuer=self._public_url,
            credential_endpoint=f"{self._public_url}/credential",
            credential_configurations_supported=metadata.credential_configurations_supported,
            authorization_servers=metadata.authorization_servers,
            nonce_endpoint=f"{self._public_url}/nonce",
            deferred_credential_endpoint=metadata.deferred_credential_endpoint,
            notification_endpoint=metadata.notification_endpoint,
            credential_response_encryption=metadata.credential_response_encryption,
            batch_credential_issuance=metadata.batch_credential_issuance,
            display=metadata.display,
        )
