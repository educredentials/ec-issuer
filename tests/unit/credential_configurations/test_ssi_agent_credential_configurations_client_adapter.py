"""Unit tests for SsiAgentCredentialTemplateClientAdapter."""

import msgspec
import pytest

from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateNotFound,
    CredentialTemplateClientError,
)
from src.credential_configurations.models import (
    CredentialTemplate,
    Display,
    Logo,
)
from src.credential_configurations.ssi_agent_credential_configurations_client_adapter import (  # noqa: E501
    SsiAgentCredentialTemplateClientAdapter,
)
from src.lib.http_client import HttpClient

from ..support.requests_doubles import MockResponse, RecordedRequest, RequestsSpy


@pytest.fixture
def http_client():
    return RequestsSpy()


@pytest.fixture
def subject(http_client: HttpClient) -> SsiAgentCredentialTemplateClientAdapter:
    return SsiAgentCredentialTemplateClientAdapter(
        ssi_agent_url="http://agent.example.com", http_client=http_client
    )


@pytest.fixture
def credential_template() -> CredentialTemplate:
    return CredentialTemplate(
        type=["VerifiableCredential"],
        id="credential_template_id",
        display=Display(name="Test Credential"),
    )


# Response from the list() endpoint — flat array of templates (each with its own ID)
_VALID_TEMPLATES_JSON = msgspec.json.encode(
    [
        {
            "type": ["VerifiableCredential"],
            "format": "jwt_vc_json",
            "id": "credential_template_id",
            "display": {
                "name": "Open Badge Credential",
                "logo": {
                    "alt_text": "Blue Logo",
                    "uri": "https://example.com/images/logo.png",
                },
            },
        }
    ]
)


# Legacy metadata response — used for old well-known endpoint tests
_VALID_METADATA_JSON = msgspec.json.encode(
    {
        "credential_issuer": "http://issuer.example.com",
        "credential_endpoint": "http://issuer.example.com/credential",
        "credential_templates_supported": {
            "credential_template_id": {
                "type": ["VerifiableCredential"],
                "format": "jwt_vc_json",
                "display": {
                    "name": "Open Badge Credential",
                    "logo": {
                        "alt_text": "Blue Logo",
                        "uri": "https://example.com/images/logo.png",
                    },
                },
            }
        },
    }
)

# Response from the POST create endpoint — a bare CredentialTemplate
_CREATE_RESPONSE_JSON = msgspec.json.encode(
    {
        "type": ["VerifiableCredential"],
        "format": "jwt_vc_json",
        "id": "credential_template_id",
        "display": {
            "name": "Test Credential",
            "logo": None,
        },
    }
)


@pytest.fixture
def valid_metadata_response() -> MockResponse:
    return MockResponse(status_code=200, _content=_VALID_TEMPLATES_JSON)


@pytest.fixture
def create_response() -> MockResponse:
    return MockResponse(status_code=200, _content=_CREATE_RESPONSE_JSON)


def _expected_payload(_template_id: str) -> dict[str, object]:
    return {
        "title": None,
        "dataModel": None,
        "holderType": None,
        "status": None,
        "description": None,
        "type": ["VerifiableCredential"],
        "display": {
            "name": "Test Credential",
        },
        "schema": {},
        "credentialExpiration": {"type": "never"},
    }


class TestSsiAgentCredentialTemplateClientAdapter:
    """Tests for the SsiAgentCredentialTemplateClientAdapter class."""

    def test_create_success(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
        create_response: MockResponse,
    ):
        http_client.set_response(create_response)
        _ = subject.create(credential_template)
        expected_request = RecordedRequest(
            method="post",
            url="http://agent.example.com/v0/create-new-template",
            json=_expected_payload(""),
        )
        assert http_client.calls[0] == expected_request

    def test_create_returns_merged_template(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
        create_response: MockResponse,
        valid_metadata_response: MockResponse,
    ):
        # The create response contains a valid template
        http_client.set_response(create_response)
        http_client.set_response(valid_metadata_response)

        result = subject.update(credential_template)

        assert result.id == "credential_template_id"

    def test_create_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
    ):
        http_client.set_response(
            MockResponse(status_code=400, _content=b'{"error": "error"}')
        )
        with pytest.raises(CredentialTemplateClientError):
            _ = subject.create(credential_template)

    def test_get_returns_matching_template(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        valid_metadata_response: MockResponse,
    ):
        expected_template = CredentialTemplate(
            type=["VerifiableCredential"],
            id="credential_template_id",
            display=Display(
                name="Open Badge Credential",
                logo=Logo(
                    alt_text="Blue Logo",
                    uri="https://example.com/images/logo.png",
                ),
            ),
        )
        http_client.set_response(valid_metadata_response)
        result = subject.get("credential_template_id")
        assert result == expected_template

    def test_list_sends_get_to_templates_endpoint(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        valid_metadata_response: MockResponse,
    ):
        http_client.set_response(valid_metadata_response)
        _ = subject.list()
        assert http_client.calls[0] == RecordedRequest(
            method="get",
            url="http://agent.example.com/v0/list-all-templates",
        )

    def test_list_returns_templates_with_ids_from_array(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
    ):
        http_client.set_response(
            MockResponse(status_code=200, _content=_VALID_TEMPLATES_JSON)
        )
        results = subject.list()
        assert len(results) == 1
        expected_template = CredentialTemplate(
            type=["VerifiableCredential"],
            id="credential_template_id",
            display=Display(
                name="Open Badge Credential",
                logo=Logo(
                    alt_text="Blue Logo",
                    uri="https://example.com/images/logo.png",
                ),
            ),
        )
        assert results[0] == expected_template

    def test_list_raises_client_error_on_upstream_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
    ):
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Server Error"')
        )
        with pytest.raises(CredentialTemplateClientError):
            _ = subject.list()

    def test_list_raises_client_error_on_invalid_response_json(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=200, _content=b"not json"))
        with pytest.raises(CredentialTemplateClientError):
            _ = subject.list()

    def test_get_raises_not_found_when_id_absent(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        valid_metadata_response: MockResponse,
    ):
        http_client.set_response(valid_metadata_response)
        with pytest.raises(CredentialTemplateNotFound):
            _ = subject.get("unknown-id")

    def test_get_propagates_client_error_from_list(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=500, _content=b'"error"'))
        with pytest.raises(CredentialTemplateClientError):
            _ = subject.get("credential_template_id")

    def test_get_raises_client_error_on_invalid_response_json(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=200, _content=b"not json"))
        with pytest.raises(CredentialTemplateClientError):
            _ = subject.get("credential_template_id")

    def test_update_sends_post_with_correct_url_and_payload(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
        create_response: MockResponse,
        valid_metadata_response: MockResponse,
    ):
        # Create response needs valid template JSON so the adapter can decode it
        http_client.set_response(create_response)
        http_client.set_response(valid_metadata_response)

        _ = subject.update(credential_template)
        assert len(http_client.calls) == 1
        assert http_client.calls[0] == RecordedRequest(
            method="post",
            url="http://agent.example.com/v0/create-new-template",
            json=_expected_payload(""),
        )

    def test_update_returns_merged_template(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
        create_response: MockResponse,
        valid_metadata_response: MockResponse,
    ):
        # First call is create -> returns a valid template
        http_client.set_response(create_response)
        # Second call is get from create -> returns merged metadata
        http_client.set_response(valid_metadata_response)

        result = subject.update(credential_template)

        assert result.id == "credential_template_id"

    def test_update_raises_not_found_on_404(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
    ):
        http_client.set_response(MockResponse(status_code=404, _content=b'"Not Found"'))
        with pytest.raises(CredentialTemplateNotFound):
            _ = subject.update(credential_template)

    def test_update_raises_client_error_on_upstream_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialTemplateClientAdapter,
        credential_template: CredentialTemplate,
    ):
        http_client.set_response(
            MockResponse(status_code=422, _content=b'"Unprocessable"')
        )
        with pytest.raises(CredentialTemplateClientError):
            _ = subject.update(credential_template)
