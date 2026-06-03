"""SSI-Agent Adapter for credential configurations operations."""

from dataclasses import asdict, dataclass
from typing import override

import msgspec
import requests

from .credential_configurations_client_port import (
    CredentialConfigurationNotFound,
    CredentialConfigurationsClientError,
    CredentialConfigurationsClientPort,
)
from .models import CredentialConfiguration


# Response model for issuer metadata
@dataclass
class _SsiAgentIssuerMetadata:
    """SSI agent issuer metadata response."""

    credential_issuer: str
    credential_endpoint: str
    credential_configurations_supported: dict[str, CredentialConfiguration]


class SsiAgentCredentialConfigurationsClientAdapter(CredentialConfigurationsClientPort):
    """Adapter for SSI Agent credential configurations API."""

    _ssi_agent_admin_base_url: str
    _ssi_agent_issuer_base_url: str
    _timeout: int

    def __init__(
        self,
        ssi_agent_url: str,
    ) -> None:
        """Initialize the adapter.

        Args:
            ssi_agent_url: The admin base URL of the SSI agent.
        """
        self._ssi_agent_admin_base_url = ssi_agent_url.rstrip("/")
        self._ssi_agent_issuer_base_url = ssi_agent_url.rstrip("/")
        self._timeout = 10

    @override
    def create(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Create a new credential configuration.

        Args:
            configuration: The credential configuration to create.

        Returns:
            The created credential configuration.

        Raises:
            CredentialConfigurationsClientError: When upstream service returns an error.
        """
        response = requests.post(
            f"{self._ssi_agent_admin_base_url}/v0/credential-configurations",
            json=asdict(configuration),
            timeout=self._timeout,
        )

        if 400 <= response.status_code < 600:
            raise CredentialConfigurationsClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

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
        response = requests.get(
            f"{self._ssi_agent_admin_base_url}/.well-known/openid-credential-issuer",
            timeout=self._timeout,
        )

        if 400 <= response.status_code < 600:
            raise CredentialConfigurationsClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        metadata: _SsiAgentIssuerMetadata = msgspec.json.decode(
            response.content, type=_SsiAgentIssuerMetadata
        )

        configurations: list[CredentialConfiguration] = []
        for id, config in metadata.credential_configurations_supported.items():
            config.credential_configuration_id = id
            configurations.append(config)

        return configurations

    @override
    def update(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Update an existing credential configuration.

        Args:
            configuration: The credential configuration to update.

        Returns:
            The updated credential configuration.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When upstream service returns an error.
        """
        # For SSI Agent, POST to /v0/credential-configurations with existing
        # ID updates it
        response = requests.post(
            f"{self._ssi_agent_admin_base_url}/v0/credential-configurations",
            json=asdict(configuration),
            timeout=self._timeout,
        )

        if response.status_code == 404:
            raise CredentialConfigurationNotFound(
                f"Configuration {configuration.credential_configuration_id} not found"
            )

        if 400 <= response.status_code < 600:
            raise CredentialConfigurationsClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        return configuration

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
