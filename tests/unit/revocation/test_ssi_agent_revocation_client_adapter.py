"""Unit tests for SsiAgentRevocationClientAdapter."""

import pytest

from src.lib.http_client import HttpClient
from src.revocation import SsiAgentRevocationClientAdapter
from src.revocation.revocation_client_port import CredentialRevocationError

from ..support.requests_doubles import MockResponse, RequestsSpy


@pytest.fixture
def http_client() -> RequestsSpy:
    """Provide a fresh RequestsSpy for each test."""
    return RequestsSpy()


@pytest.fixture
def subject(http_client: HttpClient) -> SsiAgentRevocationClientAdapter:
    """Provide the adapter wired to the spy."""
    return SsiAgentRevocationClientAdapter(
        ssi_agent_url="http://agent.example.com",
        http_client=http_client,
    )


class TestRevoke:
    """Tests for the revoke method."""

    def test_revokes_with_invalid_status(
        self,
        subject: SsiAgentRevocationClientAdapter,
        http_client: RequestsSpy,
    ) -> None:
        """Revoke sends PATCH with credentialStatus: INVALID and returns None."""
        http_client.set_response(MockResponse(status_code=200))

        result = subject.revoke("cred-123")

        assert result is None
        assert len(http_client.calls) == 1
        call = http_client.calls[0]
        assert call.method == "patch"
        assert call.url == "http://agent.example.com/v0/credentials/cred-123"
        assert call.json == {"credentialStatus": "INVALID"}

    def test_raises_on_404(
        self,
        subject: SsiAgentRevocationClientAdapter,
        http_client: RequestsSpy,
    ) -> None:
        """Revoke raises CredentialRevocationError on 404."""
        http_client.set_response(
            MockResponse(status_code=404, _content=b"Not found")
        )

        with pytest.raises(CredentialRevocationError, match="Upstream error: 404"):
            subject.revoke("cred-404")

    def test_raises_on_400(
        self,
        subject: SsiAgentRevocationClientAdapter,
        http_client: RequestsSpy,
    ) -> None:
        """Revoke raises CredentialRevocationError on 400."""
        http_client.set_response(
            MockResponse(status_code=400, _content=b"Bad request")
        )

        with pytest.raises(CredentialRevocationError, match="Upstream error: 400"):
            subject.revoke("cred-400")

    def test_raises_on_500(
        self,
        subject: SsiAgentRevocationClientAdapter,
        http_client: RequestsSpy,
    ) -> None:
        """Revoke raises CredentialRevocationError on 500."""
        http_client.set_response(
            MockResponse(status_code=500, _content=b"Server error")
        )

        with pytest.raises(CredentialRevocationError, match="Upstream error: 500"):
            subject.revoke("cred-500")

    def test_succeeds_on_201(
        self,
        subject: SsiAgentRevocationClientAdapter,
        http_client: RequestsSpy,
    ) -> None:
        """Revoke succeeds on 201 Created."""
        http_client.set_response(MockResponse(status_code=201))

        result = subject.revoke("cred-201")

        assert result is None
