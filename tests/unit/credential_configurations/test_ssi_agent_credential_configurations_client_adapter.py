"""Unit tests for SsiAgentCredentialConfigurationsClientAdapter."""

import pytest

from src.credential_configurations.credential_configurations_client_port import (
    CredentialConfigurationNotFound,
    CredentialConfigurationsClientError,
)
from src.credential_configurations.models import (
    CredentialConfiguration,
)
from src.credential_configurations.ssi_agent_credential_configurations_client_adapter import (  # noqa: E501
    SsiAgentCredentialConfigurationsClientAdapter,
)
from src.lib.http_client import HttpClient

from ..support.requests_doubles import MockResponse, RecordedRequest, RequestsSpy


@pytest.fixture
def http_client():
    return RequestsSpy()


@pytest.fixture
def subject(http_client: HttpClient) -> SsiAgentCredentialConfigurationsClientAdapter:
    return SsiAgentCredentialConfigurationsClientAdapter(
        ssi_agent_url="http://agent.example.com", http_client=http_client
    )


@pytest.fixture
def credential_configuration() -> CredentialConfiguration:
    return CredentialConfiguration(
        format="jwt_vc_json",
        display=None,
        credential_configuration_id="credential_configuration_id",
        credential_definition=None,
        cryptographic_binding_methods_supported=None,
        credential_signing_alg_values_supported=None,
        proof_types_supported=None,
    )


_VALID_METADATA_JSON = b'{"credential_issuer":"http://issuer.example.com","credential_endpoint":"http://issuer.example.com/credential","credential_configurations_supported":{"credential_configuration_id":{"format":"jwt_vc_json"}}}'


@pytest.fixture
def valid_metadata_response() -> MockResponse:
    return MockResponse(status_code=200, _content=_VALID_METADATA_JSON)


class TestSsiAgentCredentialConfigurationsClientAdapter:
    """Tests for the SsiAgentCredentialConfigurationsClientAdapter class."""

    def test_create_success(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        credential_configuration: CredentialConfiguration,
    ):
        was_created = subject.create(credential_configuration)
        expected_payload = {
            "format": "jwt_vc_json",
            "display": None,
            "credential_configuration_id": "credential_configuration_id",
            "credential_definition": None,
            "cryptographic_binding_methods_supported": None,
            "credential_signing_alg_values_supported": None,
            "proof_types_supported": None,
        }
        expected_request = RecordedRequest(
            method="post",
            url="http://agent.example.com/v0/credential-configurations",
            json=expected_payload,
        )
        assert http_client.calls[0] == expected_request
        assert was_created == credential_configuration

    def test_create_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        credential_configuration: CredentialConfiguration,
    ):
        http_client.set_response(
            MockResponse(status_code=400, _content=b'{"error": "error"}')
        )
        with pytest.raises(CredentialConfigurationsClientError):
            _ = subject.create(credential_configuration)

    def test_get_returns_matching_configuration(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        valid_metadata_response: MockResponse,
    ):
        http_client.set_response(valid_metadata_response)
        result = subject.get("credential_configuration_id")
        assert result == CredentialConfiguration(
            format="jwt_vc_json",
            credential_configuration_id="credential_configuration_id",
        )

    def test_list_sends_get_to_wellknown_url(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        valid_metadata_response: MockResponse,
    ):
        http_client.set_response(valid_metadata_response)
        _ = subject.list()
        assert http_client.calls[0] == RecordedRequest(
            method="get",
            url="http://agent.example.com/.well-known/openid-credential-issuer",
        )

    def test_list_returns_configurations_with_id_from_metadata_key(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
    ):
        http_client.set_response(
            MockResponse(
                status_code=200,
                _content=b'{"credential_issuer":"http://issuer.example.com","credential_endpoint":"http://issuer.example.com/credential","credential_configurations_supported":{"config-a":{"format":"jwt_vc_json"},"config-b":{"format":"ldp_vc"}}}',
            )
        )
        results = subject.list()
        assert len(results) == 2
        assert results[0] == CredentialConfiguration(
            format="jwt_vc_json", credential_configuration_id="config-a"
        )
        assert results[1] == CredentialConfiguration(
            format="ldp_vc", credential_configuration_id="config-b"
        )

    def test_list_raises_client_error_on_upstream_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
    ):
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Server Error"')
        )
        with pytest.raises(CredentialConfigurationsClientError):
            _ = subject.list()

    def test_list_raises_client_error_on_invalid_response_json(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=200, _content=b"not json"))
        with pytest.raises(CredentialConfigurationsClientError):
            _ = subject.list()

    def test_get_raises_not_found_when_id_absent(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        valid_metadata_response: MockResponse,
    ):
        http_client.set_response(valid_metadata_response)
        with pytest.raises(CredentialConfigurationNotFound):
            _ = subject.get("unknown-id")

    def test_get_propagates_client_error_from_list(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=500, _content=b'"error"'))
        with pytest.raises(CredentialConfigurationsClientError):
            _ = subject.get("credential_configuration_id")

    def test_get_raises_client_error_on_invalid_response_json(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
    ):
        http_client.set_response(MockResponse(status_code=200, _content=b"not json"))
        with pytest.raises(CredentialConfigurationsClientError):
            _ = subject.get("credential_configuration_id")

    def test_update_sends_post_with_correct_url_and_payload(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        credential_configuration: CredentialConfiguration,
    ):
        result = subject.update(credential_configuration)
        expected_payload = {
            "format": "jwt_vc_json",
            "display": None,
            "credential_configuration_id": "credential_configuration_id",
            "credential_definition": None,
            "cryptographic_binding_methods_supported": None,
            "credential_signing_alg_values_supported": None,
            "proof_types_supported": None,
        }
        assert http_client.calls[0] == RecordedRequest(
            method="post",
            url="http://agent.example.com/v0/credential-configurations",
            json=expected_payload,
        )
        assert result == credential_configuration

    def test_update_raises_not_found_on_404(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        credential_configuration: CredentialConfiguration,
    ):
        http_client.set_response(MockResponse(status_code=404, _content=b'"Not Found"'))
        with pytest.raises(CredentialConfigurationNotFound):
            _ = subject.update(credential_configuration)

    def test_update_raises_client_error_on_upstream_error(
        self,
        http_client: RequestsSpy,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
        credential_configuration: CredentialConfiguration,
    ):
        http_client.set_response(
            MockResponse(status_code=422, _content=b'"Unprocessable"')
        )
        with pytest.raises(CredentialConfigurationsClientError):
            _ = subject.update(credential_configuration)

    def test_delete_raises_not_implemented_error(
        self,
        subject: SsiAgentCredentialConfigurationsClientAdapter,
    ):
        with pytest.raises(NotImplementedError):
            subject.delete("credential_configuration_id")
