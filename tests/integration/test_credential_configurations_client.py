"""Integration tests: CredentialTemplateClientPort delete operation.

Tests the full call chain -- SsiAgentCredentialTemplateClientAdapter calling
the HTTP client -- with a real adapter and a spy HTTP client.
"""

import msgspec
import pytest

from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateNotFound,
    CredentialTemplateClientError,
)
from src.credential_configurations import (
    ssi_agent_credential_configurations_client_adapter as ssi_cred_adapter,
)
from src.lib.http_client import HttpClient

from tests.unit.support.requests_doubles import (
    MockResponse,
    RecordedRequest,
    RequestsSpy,
)

# Response from the list() endpoint -- flat array of templates (each with its own ID)
_VALID_TEMPLATES_JSON = msgspec.json.encode(
    [
        {
            "type": ["VerifiableCredential"],
            "format": "jwt_vc_json",
            "id": "credential_template_id",
            "display": [
                {
                    "name": "Open Badge Credential",
                    "logo": {
                        "alt_text": "Blue Logo",
                        "uri": "https://example.com/images/logo.png",
                    },
                },
            ],
        },
    ]
)


_VALID_METADATA_RESPONSE = MockResponse(
    status_code=200,
    _content=msgspec.json.encode(
        {
            "type": ["VerifiableCredential"],
            "format": "jwt_vc_json",
            "id": "credential_template_id",
            "display": [
                {
                    "name": "Open Badge Credential",
                    "logo": {
                        "alt_text": "Blue Logo",
                        "uri": "https://example.com/images/logo.png",
                    },
                },
            ],
        }
    ),
)


@pytest.fixture
def http_client() -> RequestsSpy:
    return RequestsSpy()


@pytest.fixture
def subject(
    http_client: HttpClient,
) -> ssi_cred_adapter.SsiAgentCredentialTemplateClientAdapter:
    return ssi_cred_adapter.SsiAgentCredentialTemplateClientAdapter(
        ssi_agent_url="http://agent.example.com", http_client=http_client
    )


class TestCredentialTemplateClientDelete:
    """Integration tests for CredentialTemplateClientPort delete operation."""

    def test_delete_sends_request_to_ssi_agent(
        self, http_client: RequestsSpy,
        subject: ssi_cred_adapter.SsiAgentCredentialTemplateClientAdapter,
    ) -> None:
        """Delete sends a POST to the correct URL with templateId."""
        http_client.set_response(MockResponse(status_code=204, _content=b""))
        subject.delete("template-123")
        assert len(http_client.calls) == 1
        call = http_client.calls[0]
        assert call == RecordedRequest(
            method="post",
            url="http://agent.example.com/v0/templates/delete-template",
            json={"templateId": "template-123"},
        )

    def test_delete_raises_not_found_on_404(
        self, http_client: RequestsSpy,
        subject: ssi_cred_adapter.SsiAgentCredentialTemplateClientAdapter,
    ) -> None:
        """Delete raises CredentialTemplateNotFound on 404."""
        http_client.set_response(MockResponse(status_code=404, _content=b'"Not Found"'))
        with pytest.raises(CredentialTemplateNotFound, match="template-123"):
            subject.delete("template-123")

    def test_delete_raises_client_error_on_server_error(
        self, http_client: RequestsSpy,
        subject: ssi_cred_adapter.SsiAgentCredentialTemplateClientAdapter,
    ) -> None:
        """Delete raises CredentialTemplateClientError on 500."""
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Internal server error"')
        )
        with pytest.raises(CredentialTemplateClientError, match="Upstream error"):
            subject.delete("template-123")

    def test_delete_returns_none_on_success(
        self, http_client: RequestsSpy,
        subject: ssi_cred_adapter.SsiAgentCredentialTemplateClientAdapter,
    ) -> None:
        """Delete returns None on 204 no content."""
        http_client.set_response(MockResponse(status_code=204, _content=b""))
        result = subject.delete("template-123")
        assert result is None
