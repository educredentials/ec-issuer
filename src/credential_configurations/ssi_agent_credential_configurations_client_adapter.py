"""SSI-Agent Adapter for credential configurations operations."""

from dataclasses import asdict, dataclass, field
from typing import override

import msgspec

from src.lib.http_client import HttpClient, RequestsHttpClient

from .credential_configurations_client_port import (
    CredentialTemplateNotFound,
    CredentialTemplateClientError,
    CredentialTemplateClientPort,
)
from .models import (
    CredentialTemplate,
    Display,
)


# Response model for issuer metadata
@dataclass
class _SsiAgentIssuerMetadata:
    """SSI agent issuer metadata response."""

    credential_issuer: str
    credential_endpoint: str
    credential_configurations_supported: dict[
        str, object
    ]


@dataclass
class _SsiAgentDisplay:
    """Display information for a credential configuration."""

    name: str | None = None
    locale: str | None = None
    logo: dict[str, str | None] | None = None
    description: str | None = None

    @staticmethod
    def from_display_info(display: Display) -> "_SsiAgentDisplay":
        logo: dict[str, str | None] | None = None
        if display.logo is not None:
            logo = {"uri": display.logo.uri, "alt_text": display.logo.alt_text}
        return _SsiAgentDisplay(
            name=display.name,
            logo=logo,
        )


@dataclass
class _SsiAgentAddPayload:
    """Payload for Create (and therefore update) credential configuration on service"""

    title: str | None = None
    dataModel: str | None = None
    holderType: str | None = None
    status: str | None = None
    description: str | None = None
    type: list[str] | None = None
    display: _SsiAgentDisplay | None = None
    schema: dict[str, object] | None = None
    credentialExpiration: dict[str, str] = field(
        default_factory=lambda: {"type": "never"},
    )

    @staticmethod
    def from_credential_template(
        template: CredentialTemplate,
    ) -> "_SsiAgentAddPayload":
        display_list: _SsiAgentDisplay | None = None
        if template.display is not None:
            display_list = _SsiAgentDisplay.from_display_info(template.display)

        return _SsiAgentAddPayload(
            title=template.title,
            dataModel=template.dataModel,
            holderType=template.holderType,
            status=template.status,
            type=template.type,
            description=template.description,
            schema=template.schema,
            display=display_list,
        )


class SsiAgentCredentialTemplateClientAdapter(CredentialTemplateClientPort):
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
    def create(self, template: CredentialTemplate) -> CredentialTemplate:
        """Create a new credential template.

        Args:
            template: The credential configuration to create.

        Returns:
            The created credential template.

        Raises:
            CredentialTemplateClientError: When upstream service returns an error.
            ValueError: When the credential configuration ID is not set.
        """
        payload = _SsiAgentAddPayload.from_credential_template(template)
        payload_dict = asdict(payload)
        url = f"{self._ssi_agent_admin_base_url}/v0/create-new-template"

        response = self._http_client.post(url, json=payload_dict)

        if response.status_code == 404:
            raise CredentialTemplateNotFound(f"Template {template.id} not found")

        if 400 <= response.status_code < 600:
            raise CredentialTemplateClientError(
                f"Upstream error: {response.status_code} - {response.text}"
            )

        try:
            template: CredentialTemplate = msgspec.json.decode(
                response.content, type=CredentialTemplate
            )
        except msgspec.DecodeError as e:
            raise CredentialTemplateClientError(
                f"Invalid response from upstream: {e}"
            ) from e

        return template

    @override
    def list(self) -> list[CredentialTemplate]:
        """List all credential templates.

        Calls /v0/templates/get-all-templates and decodes the response
        as a dict of templates keyed by ID.

        Returns:
            A list of all credential templates.

        Raises:
            CredentialTemplateClientError: When upstream service returns an error.
        """
        response = self._http_client.get(
            f"{self._ssi_agent_admin_base_url}/v0/list-all-templates",
        )

        if 400 <= response.status_code < 600:
            raise CredentialTemplateClientError(
                f"Upstream error: {response.status_code} - {response.text}"
            )

        try:
            templates: list[CredentialTemplate] = msgspec.json.decode(
                response.content, type=list[CredentialTemplate]
            )
        except msgspec.DecodeError as e:
            raise CredentialTemplateClientError(
                f"Invalid response from upstream: {e}"
            ) from e

        return templates

    @override
    def get(self, template_id: str) -> CredentialTemplate:
        """Retrieve a credential template by ID.

        Args:
            template_id: The unique credential template identifier.

        Returns:
            The matching CredentialTemplate.

        Raises:
            CredentialTemplateNotFound: When not found.
            CredentialTemplateClientError: When upstream service returns an error.
        """
        all = self.list()

        for template in all:
            if template.id == template_id:
                return template

        raise CredentialTemplateNotFound(template_id)

    @override
    def update(self, configuration: CredentialTemplate) -> CredentialTemplate:
        """Update an existing credential template.

        Implemented by "create" with an existing id.
        See self.create()
        """
        return self.create(configuration)
