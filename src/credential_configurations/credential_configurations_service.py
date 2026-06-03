"""Service for credential configurations operations."""

from .credential_configurations_client_port import CredentialConfigurationsClientPort
from .models import CredentialConfiguration


class CredentialConfigurationsService:
    """Service that executes operations for credential configurations."""

    _client: CredentialConfigurationsClientPort

    def __init__(self, client: CredentialConfigurationsClientPort) -> None:
        """Initialize the service.

        Args:
            client: The port implementation for credential configurations operations.
        """
        self._client = client

    def create(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Create a new credential configuration.

        Args:
            configuration: The credential configuration to create.

        Returns:
            The created credential configuration.

        Raises:
            CredentialConfigurationsClientError: When creation fails.
        """
        return self._client.create(configuration)

    def get(self, configuration_id: str) -> CredentialConfiguration:
        """Retrieve a credential configuration by ID.

        Args:
            configuration_id: The unique credential configuration identifier.

        Returns:
            The matching CredentialConfiguration.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When retrieval fails.
        """
        return self._client.get(configuration_id)

    def list(self) -> list[CredentialConfiguration]:
        """List all credential configurations.

        Returns:
            A list of all credential configurations.

        Raises:
            CredentialConfigurationsClientError: When listing fails.
        """
        return self._client.list()

    def update(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Update an existing credential configuration.

        Args:
            configuration: The credential configuration to update.

        Returns:
            The updated credential configuration.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When update fails.
        """
        return self._client.update(configuration)

    def delete(self, configuration_id: str) -> None:
        """Delete a credential configuration.

        Args:
            configuration_id: The unique credential configuration identifier.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When deletion fails.
        """
        return self._client.delete(configuration_id)
