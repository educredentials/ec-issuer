"""Client port for credential configurations operations."""

from abc import ABC, abstractmethod

from .models import CredentialTemplate


class CredentialTemplateNotFound(Exception):
    """Error raised when a credential configuration is not found."""


class CredentialTemplateClientError(Exception):
    """Error raised when credential configurations client operations fail."""


class CredentialTemplateClientPort(ABC):
    """Client port: Operations for credential configurations."""

    @abstractmethod
    def create(self, template: CredentialTemplate) -> CredentialTemplate:
        """Create a new credential template.

        Args:
            template: The credential template to create.

        Returns:
            The created credential configuration.

        Raises:
            CredentialTemplateClientError: When creation fails.
        """
        ...

    @abstractmethod
    def list(self) -> list[CredentialTemplate]:
        """List all credential templates.

        Returns:
            A list of all credential templates.

        Raises:
            CredentialTemplateClientError: When listing fails.
        """
        ...

    @abstractmethod
    def get(self, template_id: str) -> CredentialTemplate:
        """Retrieve a credential template by ID.

        Args:
            configuration_id: The unique credential template identifier.

        Returns:
            The matching CredentialTemplate.

        Raises:
            CredentialTemplateNotFound: When not found.
            CredentialTemplateClientError: When retrieval fails.
        """
        ...

    @abstractmethod
    def update(self, configuration: CredentialTemplate) -> CredentialTemplate:
        """Update an existing credential configuration.

        Args:
            configuration: The credential configuration to update.

        Returns:
            The updated credential configuration.

        Raises:
            CredentialTemplateNotFound: When not found.
            CredentialTemplateClientError: When update fails.
        """
        ...

    @abstractmethod
    def delete(self, template_id: str) -> None:
        """Delete a credential template by ID.

        Args:
            template_id: The unique credential template identifier.

        Raises:
            CredentialTemplateNotFound: When the template is not found.
            CredentialTemplateClientError: When deletion fails.
        """
        ...
