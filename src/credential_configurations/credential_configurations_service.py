"""Service for credential configurations operations."""

from typing import TYPE_CHECKING

from .models import CredentialTemplate

if TYPE_CHECKING:
    from .credential_configurations_client_port import (
        CredentialTemplateClientPort,
    )


class CredentialTemplateService:
    """Service that executes operations for credential configurations."""

    _client: "CredentialTemplateClientPort"

    def __init__(self, client: "CredentialTemplateClientPort") -> None:
        """Initialize the service.

        Args:
            client: The port implementation for credential configurations operations.
        """
        self._client = client

    def create(self, configuration: CredentialTemplate) -> CredentialTemplate:
        """Create a new credential configuration.

        Args:
            configuration: The credential configuration to create.

        Returns:
            The created credential configuration.

        Raises:
            CredentialTemplateClientError: When creation fails.
        """
        return self._client.create(configuration)

    def get(self, template_id: str) -> CredentialTemplate:
        """Retrieve a credential template by ID.

        Args:
            template_id: The unique credential template identifier.

        Returns:
            The matching CredentialTemplate.

        Raises:
            CredentialTemplateNotFound: When not found.
            CredentialTemplateClientError: When retrieval fails.
        """
        return self._client.get(template_id)

    def list(self) -> list[CredentialTemplate]:
        """List all credential configurations.

        Returns:
            A list of all credential configurations.

        Raises:
            CredentialTemplateClientError: When listing fails.
        """
        return self._client.list()

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
        return self._client.update(configuration)

    def ensure_by_title(
        self,
        template: CredentialTemplate,
        ssi_agent_url: str = "",
    ) -> CredentialTemplate:
        """Find an existing template by title, or create the template.

        Searches the SSI Agent for a template with a matching title.
        If one exists, it is returned. Otherwise the new template is
        created and the created result is returned.

        Args:
            template: The template to ensure exists on the SSI Agent.
            ssi_agent_url: The SSI Agent URL, included in error messages.

        Returns:
            The matching or newly created CredentialTemplate.

        Raises:
            RuntimeError: When the SSI Agent is unreachable or creation fails.
        """
        import requests

        from src.credential_configurations.credential_configurations_client_port import (  # noqa: E501
            CredentialTemplateClientError,
        )

        try:
            templates = self._client.list()
        except (requests.RequestException, CredentialTemplateClientError) as e:
            raise RuntimeError(
                f"Failed to reach SSI Agent {ssi_agent_url}: {e}"
            ) from e

        for t in templates:
            if t.title == template.title:
                return t

        try:
            return self._client.create(template)
        except (requests.RequestException, CredentialTemplateClientError) as e:
            raise RuntimeError(
                f"Failed to create credential template on {ssi_agent_url}: {e}"
            ) from e
