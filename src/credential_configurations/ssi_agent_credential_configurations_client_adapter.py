"""SSI-Agent Adapter for credential configurations operations."""

from dataclasses import asdict, dataclass
from typing import override

import msgspec

from src.lib.http_client import HttpClient, RequestsHttpClient

from .credential_configurations_client_port import (
    CredentialConfigurationNotFound,
    CredentialConfigurationsClientError,
    CredentialConfigurationsClientPort,
)
from .models import (
    CredentialConfiguration,
    Display,
)


# Response model for issuer metadata
@dataclass
class _SsiAgentIssuerMetadata:
    """SSI agent issuer metadata response."""

    credential_issuer: str
    credential_endpoint: str
    credential_configurations_supported: dict[str, CredentialConfiguration]


@dataclass
class _SsiAgentDisplay:
    """Display information for a credential configuration."""

    name: str | None = None
    locale: str | None = None
    logo: dict[str, str | None] | None = None

    @staticmethod
    def from_configuration(configuration: Display) -> "_SsiAgentDisplay":
        return _SsiAgentDisplay(
            name=configuration.name,
            logo=configuration.logo,
            locale=configuration.locale,
        )


@dataclass
class _SsiAgentAddPayload:
    """Payload for Create (and therefore update) credential configuration on service"""

    credential_configuration_id: str | None = None
    format: str | None = None
    type: list[str] | None = None
    display: list[_SsiAgentDisplay] | None = None

    @staticmethod
    def from_credential_configuration(
        configuration: CredentialConfiguration,
    ) -> "_SsiAgentAddPayload":
        assert configuration.credential_definition is not None, (
            "`.credential_definition.type` is required, and must be a list of strings"
        )
        type_list = configuration.credential_definition.type

        if configuration.credential_metadata.display is None:
            displays = []
        else:
            displays = [
                _SsiAgentDisplay.from_configuration(display)
                for display in configuration.credential_metadata.display
            ]

        return _SsiAgentAddPayload(
            credential_configuration_id=configuration.credential_configuration_id,
            format=configuration.format,
            type=type_list,
            display=displays,
        )


class SsiAgentCredentialConfigurationsClientAdapter(CredentialConfigurationsClientPort):
    """Adapter for SSI Agent credential configurations API."""

    _ssi_agent_admin_base_url: str
    _ssi_agent_issuer_base_url: str
    _http_client: HttpClient

    def __init__(
        self,
        ssi_agent_url: str,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            ssi_agent_url: The admin base URL of the SSI agent.
            http_client: The HTTP client to use for requests.
                Defaults to requests module.
        """
        self._ssi_agent_admin_base_url = ssi_agent_url.rstrip("/")
        self._ssi_agent_issuer_base_url = ssi_agent_url.rstrip("/")
        if http_client is not None:
            self._http_client = http_client
        else:
            self._http_client = RequestsHttpClient()

    @override
    def create(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Create a new credential configuration.

        Args:
            configuration: The credential configuration to create.

        Returns:
            The created credential configuration.

        Raises:
            CredentialConfigurationsClientError: When upstream service returns an error.
            ValueError: When the credential configuration ID is not set.
        """
        payload = _SsiAgentAddPayload.from_credential_configuration(configuration)

        # For SSI Agent, POST to /v0/credential-configurations with existing
        # ID updates it
        response = self._http_client.post(
            f"{self._ssi_agent_admin_base_url}/v0/credential-configurations",
            json=asdict(payload),
        )

        if response.status_code == 404:
            raise CredentialConfigurationNotFound(
                f"Configuration {configuration.credential_configuration_id} not found"
            )

        if 400 <= response.status_code < 600:
            raise CredentialConfigurationsClientError(
                f"Upstream error: {response.status_code} - {response.text}"
            )

        # Rather than returning the input, we re-fetch it, so we get the result as it is
        # merged and enriched with the issuer config.
        configuration = self.get(configuration.credential_configuration_id)
        return configuration

    @override
    def get(self, configuration_id: str) -> CredentialConfiguration:
        """Retrieve a credential configuration by ID.

        Args:
            configuration_id: The unique credential configuration identifier.

        Returns:
            The matching CredentialConfiguration.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When upstream service returns an error.
        """
        # Get issuer metadata which contains all credential configurations
        all = self.list()

        # Find by credential_configuration_id
        for config in all:
            if config.credential_configuration_id == configuration_id:
                return config

        raise CredentialConfigurationNotFound(configuration_id)

    @override
    def list(self) -> list[CredentialConfiguration]:
        """List all credential configurations.

        Returns:
            A list of all credential configurations.

        Raises:
            CredentialConfigurationsClientError: When upstream service returns an error.
        """
        response = self._http_client.get(
            f"{self._ssi_agent_admin_base_url}/.well-known/openid-credential-issuer",
        )

        if 400 <= response.status_code < 600:
            raise CredentialConfigurationsClientError(
                f"Upstream error: {response.status_code} - {response.text}"
            )

        try:
            metadata: _SsiAgentIssuerMetadata = msgspec.json.decode(
                response.content, type=_SsiAgentIssuerMetadata
            )
        except msgspec.DecodeError as e:
            raise CredentialConfigurationsClientError(
                f"Invalid response from upstream: {e}"
            ) from e

        configurations: list[CredentialConfiguration] = []
        for (
            id,
            configuration,
        ) in metadata.credential_configurations_supported.items():
            configuration.credential_configuration_id = id
            configurations.append(configuration)

        return configurations

    @override
    def update(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Update an existing credential configuration.

        Implemented by "create" with an existing id.
        See self.create()
        """
        return self.create(configuration)

    @override
    def delete(self, configuration_id: str) -> None:
        """Delete a credential configuration.

        Args:
            configuration_id: The unique credential configuration identifier.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When upstream service returns an error.
        """
        raise NotImplementedError(
            "Delete is not implemented for credential configurations"
        )
