"""Unit tests for the Proxyrequests.IssuerAgentAdapter."""

from typing import override

import pytest
from requests.exceptions import HTTPError, ReadTimeout

from src.issuer_agent.issuer_agent_port import MetadataError
from src.issuer_agent.ssi_agent_adapter import (
    SsiAgentAdapter,
    SsiAgentHttpClient,
    SsiAgentHttpResponse,
)
from tests.unit.test_doubles import ConfigRepoStub


class SsiAgentResponseStub(SsiAgentHttpResponse):
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


class SsiAgentResponseRedirectStub(SsiAgentHttpResponse):
    """Stub: returns a 302 redirect response."""

    @property
    @override
    def status_code(self) -> int:
        return 302

    @property
    @override
    def content(self) -> bytes:
        return "".encode()


class SsiAgentClientStub(SsiAgentHttpClient):
    """Stub: always returns a successful 200 response."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Return a successful response stub."""
        return SsiAgentResponseStub()


class SsiAgentClientErrorStub(SsiAgentHttpClient):
    """Stub: always raises HTTPError."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Raise an HTTP error."""
        raise HTTPError


class SsiAgentClientTimeoutStub(SsiAgentHttpClient):
    """Stub: always raises ReadTimeout."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Raise a timeout error."""
        raise ReadTimeout


class SsiAgentClientRedirectStub(SsiAgentHttpClient):
    """Stub: always returns a 302 redirect response."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Return a redirect response stub."""
        return SsiAgentResponseRedirectStub()


class TestSsiAgentAdapterGetCredentialIssuerMetadata:
    """Test the ProxyIssuerAgentAdapter."""

    def test_credential_issuer_metadata_timeout(self):
        """Test that the proxy adapter has a hardcoded timeout."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(
            config=config, requests_client=SsiAgentClientTimeoutStub()
        )

        with pytest.raises(ReadTimeout):
            _ = subject.credential_issuer_metadata()

    def test_credential_issuer_metadata_error(self):
        """Test that the proxy adapter proxies 4xx errors."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(
            config=config, requests_client=SsiAgentClientErrorStub()
        )

        with pytest.raises(HTTPError):
            _ = subject.credential_issuer_metadata()

    def test_credential_issuer_metadata_3xx_redirect(self):
        """Test proxy adapter handles 3xx redirects with not supported response."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(
            config=config, requests_client=SsiAgentClientRedirectStub()
        )

        with pytest.raises(MetadataError):
            _ = subject.credential_issuer_metadata()

    def test_credential_issuer_metadata_200_success(self):
        """Test that the proxy adapter returns successful responses."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(config=config, requests_client=SsiAgentClientStub())

        metadata = subject.credential_issuer_metadata()
        assert metadata.credential_issuer == "http://example.com/issuer"
