"""Unit tests for the Proxyrequests.IssuerAgentAdapter."""

from typing import override

import pytest
from requests.exceptions import HTTPError, ReadTimeout

from src.config.config_port import ConfigRepoPort
from src.issuer_agent.ssi_agent_adapter import (
    MetadataError,
    SsiAgentAdapter,
    SsiAgentHttpClient,
    SsiAgentHttpResponse,
)


class MockConfigRepo(ConfigRepoPort):
    """Mock configuration repository for testing."""

    def __init__(self, issuer_agent_base_url: str = "http://example.com"):
        self.server_host: str = "localhost"
        self.server_port: int = 8080
        self.issuer_agent_base_url: str = issuer_agent_base_url
        self.debug: bool = False


class MockResponse(SsiAgentHttpResponse):
    """Mock response for testing."""

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


class MockResponseRedirect(SsiAgentHttpResponse):
    @property
    @override
    def status_code(self) -> int:
        return 302

    @property
    @override
    def content(self) -> bytes:
        return "".encode()


class MockRequestsClient(SsiAgentHttpClient):
    """Simple POPO mock for HTTP client that implements RequestsClientProtocol."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        return MockResponse()


class MockRequestsClientError(SsiAgentHttpClient):
    """Simple POPO mock for HTTP client that implements RequestsClientProtocol."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        raise HTTPError


class MockRequestsClientTimeout(SsiAgentHttpClient):
    """Simple POPO mock for HTTP client that implements RequestsClientProtocol."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        raise ReadTimeout


class MockRequestsClientRedirect(SsiAgentHttpClient):
    """Simple POPO mock for HTTP client that implements RequestsClientProtocol."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        return MockResponseRedirect()


class TestSsiAgentAdapterGetCredentialIssuerMetadata:
    """Test the ProxyIssuerAgentAdapter."""

    def test_credential_issuer_metadata_timeout(self):
        """Test that the proxy adapter has a hardcoded timeout."""
        config = MockConfigRepo()
        mock_client = MockRequestsClientTimeout()
        subject = SsiAgentAdapter(config=config, requests_client=mock_client)

        with pytest.raises(ReadTimeout):
            _ = subject.credential_issuer_metadata()

    def test_credential_issuer_metadata_error(self):
        """Test that the proxy adapter proxies 4xx errors."""
        config = MockConfigRepo()
        mock_client = MockRequestsClientError()
        subject = SsiAgentAdapter(config=config, requests_client=mock_client)

        with pytest.raises(HTTPError):
            _ = subject.credential_issuer_metadata()

    def test_credential_issuer_metadata_3xx_redirect(self):
        """Test proxy adapter handles 3xx redirects with not supported response."""
        config = MockConfigRepo()
        mock_client = MockRequestsClientRedirect()
        subject = SsiAgentAdapter(config=config, requests_client=mock_client)

        with pytest.raises(MetadataError):
            _ = subject.credential_issuer_metadata()

    def test_credential_issuer_metadata_200_success(self):
        """Test that the proxy adapter returns successful responses."""
        config = MockConfigRepo()
        mock_client = MockRequestsClient()
        subject = SsiAgentAdapter(config=config, requests_client=mock_client)

        metadata = subject.credential_issuer_metadata()
        assert metadata.credential_issuer == "http://example.com/issuer"
