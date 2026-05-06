"""Unit tests for SsiAgentMetadataRepository."""

from typing import override

import pytest
from requests.exceptions import HTTPError, ReadTimeout

from src.metadata.metadata_repository import MetadataNotFoundError
from src.metadata.ssi_agent_metadata_adapter import (
    SsiAgentMetadataAdapter,
    SsiAgentMetadataHttpClient,
    SsiAgentMetadataHttpResponse,
)
from tests.unit.test_doubles import ConfigRepoStub


class SsiAgentMetadataResponseStub(SsiAgentMetadataHttpResponse):
    """Stub: returns a 200 response with hardcoded credential issuer metadata."""

    @property
    @override
    def status_code(self) -> int:
        return 200

    @property
    @override
    def content(self) -> bytes:
        return b"""{
        "credential_issuer": "http://example.com/issuer",
        "credential_endpoint": "http://example.com/credential",
        "credential_configurations_supported": {}
        }"""


class SsiAgentMetadataResponseRedirectStub(SsiAgentMetadataHttpResponse):
    """Stub: returns a 302 redirect response."""

    @property
    @override
    def status_code(self) -> int:
        return 302

    @property
    @override
    def content(self) -> bytes:
        return "".encode()


class SsiAgentMetadataResponseErrorStub(SsiAgentMetadataHttpResponse):
    """Stub: returns a 404 error response."""

    @property
    @override
    def status_code(self) -> int:
        return 404

    @property
    @override
    def content(self) -> bytes:
        return b"Not Found"


class SsiAgentMetadataClientStub(SsiAgentMetadataHttpClient):
    """Stub: always returns a successful 200 response."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Return a successful response stub."""
        return SsiAgentMetadataResponseStub()


class SsiAgentMetadataClientErrorStub(SsiAgentMetadataHttpClient):
    """Stub: always raises HTTPError."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Raise an HTTP error."""
        raise HTTPError


class SsiAgentMetadataClientTimeoutStub(SsiAgentMetadataHttpClient):
    """Stub: always raises ReadTimeout."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Raise a timeout error."""
        raise ReadTimeout


class SsiAgentMetadataClientRedirectStub(SsiAgentMetadataHttpClient):
    """Stub: always returns a 302 redirect response."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Return a redirect response stub."""
        return SsiAgentMetadataResponseRedirectStub()


class SsiAgentMetadataClientErrorResponseStub(SsiAgentMetadataHttpClient):
    """Stub: always returns a 404 error response."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentMetadataHttpResponse:
        """Return an error response stub."""
        return SsiAgentMetadataResponseErrorStub()


class TestSsiAgentMetadataAdapterGetCredentialIssuerMetadata:
    """Test the SsiAgentMetadataAdapter."""

    def test_get_credential_issuer_metadata_timeout(self):
        """Test that the adapter has a hardcoded timeout."""
        config = ConfigRepoStub()
        subject = SsiAgentMetadataAdapter(
            config=config, requests_client=SsiAgentMetadataClientTimeoutStub()
        )

        with pytest.raises(ReadTimeout):
            _ = subject.get()

    def test_get_credential_issuer_metadata_http_error(self):
        """Test that the adapter raises error on HTTP errors."""
        config = ConfigRepoStub()
        subject = SsiAgentMetadataAdapter(
            config=config, requests_client=SsiAgentMetadataClientErrorStub()
        )

        with pytest.raises(HTTPError):
            _ = subject.get()

    def test_get_credential_issuer_metadata_3xx_redirect(self):
        """Test adapter handles 3xx redirects with MetadataNotFoundError."""
        config = ConfigRepoStub()
        subject = SsiAgentMetadataAdapter(
            config=config, requests_client=SsiAgentMetadataClientRedirectStub()
        )

        with pytest.raises(MetadataNotFoundError):
            _ = subject.get()

    def test_get_credential_issuer_metadata_404_error(self):
        """Test adapter handles 404 errors with MetadataNotFoundError."""
        config = ConfigRepoStub()
        subject = SsiAgentMetadataAdapter(
            config=config, requests_client=SsiAgentMetadataClientErrorResponseStub()
        )

        with pytest.raises(MetadataNotFoundError):
            _ = subject.get()

    def test_get_credential_issuer_metadata_200_success(self):
        """Test that the adapter returns successful responses."""
        config = ConfigRepoStub()
        subject = SsiAgentMetadataAdapter(
            config=config, requests_client=SsiAgentMetadataClientStub()
        )

        metadata = subject.get()
        assert metadata.credential_issuer == "http://example.com/issuer"

    def test_store_not_supported(self):
        """Test that store raises NotImplementedError."""
        config = ConfigRepoStub()
        subject = SsiAgentMetadataAdapter(config=config)

        from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata

        with pytest.raises(NotImplementedError):
            subject.store(
                CredentialIssuerMetadata(
                    credential_issuer="https://example.com",
                    credential_endpoint="https://example.com/credential",
                    credential_configurations_supported={},
                )
            )
