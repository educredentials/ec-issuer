"""Client port for credential configurations operations."""

from abc import ABC, abstractmethod

from .models import CredentialConfiguration


class CredentialConfigurationNotFound(Exception):
    """Error raised when a credential configuration is not found."""


class CredentialConfigurationsClientError(Exception):
    """Error raised when credential configurations client operations fail."""


class CredentialConfigurationsClientPort(ABC):
    """Client port: Operations for credential configurations."""

    @abstractmethod
    def create(self, configuration: CredentialConfiguration) -> CredentialConfiguration:
        """Create a new credential configuration.

        Args:
            configuration: The credential configuration to create.

        Returns:
            The created credential configuration.

        Raises:
            CredentialConfigurationsClientError: When creation fails.
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def list(self) -> list[CredentialConfiguration]:
        """List all credential configurations.

        Returns:
            A list of all credential configurations.

        Raises:
            CredentialConfigurationsClientError: When listing fails.
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def delete(self, configuration_id: str) -> None:
        """Delete a credential configuration.

        Args:
            configuration_id: The unique credential configuration identifier.

        Raises:
            CredentialConfigurationNotFound: When not found.
            CredentialConfigurationsClientError: When deletion fails.
        """
        ...
