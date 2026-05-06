"""Unit tests for SsiAgentAdapter (offer/credential operations)."""

import msgspec
from typing import override

import pytest

from src.credentials.credential import Credential, CredentialResponse
from src.issuer_agent.issuer_agent_port import IssuerAgentError
from src.issuer_agent.ssi_agent_adapter import (
    SsiAgentAdapter,
    SsiAgentHttpClient,
    SsiAgentHttpResponse,
)
from tests.unit.test_doubles import ConfigRepoStub


class SsiAgentResponseStub(SsiAgentHttpResponse):
    """Stub: returns a 200 response with valid CredentialResponse."""

    @property
    @override
    def status_code(self) -> int:
        return 200

    @property
    @override
    def content(self) -> bytes:
        response = CredentialResponse(credentials=[Credential(credential="test")])
        return msgspec.json.encode(response)


class SsiAgentResponseErrorStub(SsiAgentHttpResponse):
    """Stub: returns a 500 error response."""

    @property
    @override
    def status_code(self) -> int:
        return 500

    @property
    @override
    def content(self) -> bytes:
        return b"Internal Server Error"


class SsiAgentResponseNonceStub(SsiAgentHttpResponse):
    """Stub: returns a 200 response with nonce."""

    @property
    @override
    def status_code(self) -> int:
        return 200

    @property
    @override
    def content(self) -> bytes:
        return b'{"c_nonce": "test-nonce-123"}'


class SsiAgentClientStub(SsiAgentHttpClient):
    """Stub: returns successful responses for POST requests."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Raise NotImplementedError - SsiAgentAdapter doesn't use GET."""
        raise NotImplementedError

    @override
    def post(
        self,
        url: str,
        data: bytes,
        headers: dict[str, str],
        timeout: int,
    ) -> SsiAgentHttpResponse:
        """Return a successful response stub."""
        if "/nonce" in url:
            return SsiAgentResponseNonceStub()
        return SsiAgentResponseStub()


class SsiAgentClientErrorStub(SsiAgentHttpClient):
    """Stub: returns error responses for POST requests."""

    @override
    def get(self, url: str, timeout: int) -> SsiAgentHttpResponse:
        """Raise NotImplementedError."""
        raise NotImplementedError

    @override
    def post(
        self,
        url: str,
        data: bytes,
        headers: dict[str, str],
        timeout: int,
    ) -> SsiAgentHttpResponse:
        """Return an error response stub."""
        return SsiAgentResponseErrorStub()


class TestSsiAgentAdapterCredentialRequest:
    """Test the SsiAgentAdapter credential request operations."""

    def test_credential_request_success(self):
        """Test that credential_request proxies to the SSI agent."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(config=config, requests_client=SsiAgentClientStub())

        # This should not raise - it proxies to the agent
        _ = subject.credential_request(
            format="test",
            credential_configuration_id="test",
            proof={},
            issuer_state="test",
            access_token="test",
        )

    def test_credential_request_upstream_error(self):
        """Test that credential_request propagates upstream errors."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(
            config=config, requests_client=SsiAgentClientErrorStub()
        )

        with pytest.raises(IssuerAgentError):
            _ = subject.credential_request(
                format="test",
                credential_configuration_id="test",
                proof={},
                issuer_state="test",
                access_token="test",
            )

    def test_request_nonce_success(self):
        """Test that request_nonce proxies to the SSI agent."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(config=config, requests_client=SsiAgentClientStub())

        _ = subject.request_nonce()

    def test_request_nonce_upstream_error(self):
        """Test that request_nonce propagates upstream errors."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(
            config=config, requests_client=SsiAgentClientErrorStub()
        )

        with pytest.raises(IssuerAgentError):
            _ = subject.request_nonce()

    def test_credential_issuer_metadata_not_supported(self):
        """Test that credential_issuer_metadata raises NotImplementedError."""
        config = ConfigRepoStub()
        subject = SsiAgentAdapter(config=config)

        with pytest.raises(NotImplementedError):
            _ = subject.credential_issuer_metadata()
