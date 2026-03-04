"""Unit tests for the ProxyIssuerAgentAdapter."""

from typing import Any

from src.config import ConfigRepo
from src.issuer_agent_adapter import (
    RequestProtocol,
    RequestsClientProtocol,
    ResponseProtocol,
)
from src.issuer_agent_adapter.proxy_adapter import ProxyIssuerAgentAdapter


class MockConfigRepo(ConfigRepo):
    """Mock configuration repository for testing."""

    def __init__(self, issuer_agent_base_url: str = "http://example.com"):
        self.server_host = "localhost"
        self.server_port = 8080
        self.issuer_agent_base_url = issuer_agent_base_url


class MockResponse(ResponseProtocol):
    """Simple POPO mock for HTTP responses that implements ResponseProtocol."""

    def __init__(
        self,
        status_code: int,
        content: bytes,
        json_data: dict[str, Any] | None = None,
    ) -> None:
        self._status_code = status_code
        self._content = content
        self._json_data = json_data or {}

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def content(self) -> bytes:
        return self._content

    def json(self) -> dict[str, Any]:
        return self._json_data


class MockRequestsClient(RequestsClientProtocol):
    """Simple POPO mock for HTTP client that implements RequestsClientProtocol."""

    def __init__(self, response: MockResponse) -> None:
        self._response = response

    def get(self, url: str, timeout: int) -> MockResponse:
        return self._response


class MockRequest(RequestProtocol):
    """Simple POPO mock for Flask request that implements RequestProtocol."""

    pass


class TestProxyIssuerAgentAdapter:
    """Test the ProxyIssuerAgentAdapter."""

    def test_credential_issuer_metadata_timeout(self):
        """Test that the proxy adapter has a hardcoded timeout."""
        config = MockConfigRepo()
        mock_response = MockResponse(
            status_code=200,
            content=b'{"key": "value"}',
            json_data={"key": "value"},
        )
        mock_client = MockRequestsClient(mock_response)
        subject = ProxyIssuerAgentAdapter(config=config, requests_client=mock_client)

        assert subject.timeout == 10

    def test_credential_issuer_metadata_4xx_error(self):
        """Test that the proxy adapter proxies 4xx errors."""
        config = MockConfigRepo()
        mock_response = MockResponse(status_code=404, content=b"Not Found")
        mock_client = MockRequestsClient(mock_response)
        subject = ProxyIssuerAgentAdapter(config=config, requests_client=mock_client)
        mock_request = MockRequest()

        response = subject.credential_issuer_metadata(mock_request)
        assert response.status_code == 404
        assert response.content == b"Not Found"

    def test_credential_issuer_metadata_5xx_error(self):
        """Test that the proxy adapter proxies 5xx errors."""
        config = MockConfigRepo()
        mock_response = MockResponse(status_code=500, content=b"Internal Server Error")
        mock_client = MockRequestsClient(mock_response)
        subject = ProxyIssuerAgentAdapter(config=config, requests_client=mock_client)
        mock_request = MockRequest()

        response = subject.credential_issuer_metadata(mock_request)
        assert response.status_code == 500
        assert response.content == b"Internal Server Error"

    def test_credential_issuer_metadata_3xx_redirect(self):
        """Test proxy adapter handles 3xx redirects with not supported response."""
        config = MockConfigRepo()
        mock_response = MockResponse(status_code=302, content=b"")
        mock_client = MockRequestsClient(mock_response)
        subject = ProxyIssuerAgentAdapter(config=config, requests_client=mock_client)
        mock_request = MockRequest()

        response = subject.credential_issuer_metadata(mock_request)
        assert response.status_code == 400
        assert response.content == b'{"error": "Redirects not supported"}'
        assert response.json() == {"error": "Redirects not supported"}

    def test_credential_issuer_metadata_200_success(self):
        """Test that the proxy adapter returns successful responses."""
        config = MockConfigRepo()
        mock_response = MockResponse(
            status_code=200, content=b'{"key": "value"}', json_data={"key": "value"}
        )
        mock_client = MockRequestsClient(mock_response)
        subject = ProxyIssuerAgentAdapter(config=config, requests_client=mock_client)
        mock_request = MockRequest()

        response = subject.credential_issuer_metadata(mock_request)
        assert response.status_code == 200
        assert response.content == b'{"key": "value"}'
        assert response.json() == {"key": "value"}
