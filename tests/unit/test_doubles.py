"""Shared test doubles for unit tests.

See docs/src/test_doubles.md for naming conventions and rules.
"""

from typing import override

from src.access_control.access_control_port import AccessControlPort
from src.config.config_port import ConfigRepoPort
from src.credentials.credential import CredentialResponse
from src.issuer_agent.issuer_agent_port import IssuerAgentPort
from src.metadata.credential_issuer_metadata import (
    CredentialConfiguration,
    CredentialIssuerMetadata,
)
from src.metadata.metadata_service import MetadataService
from src.offers.in_memory_adapter import InMemoryOffersRepository
from src.offers.offer_repository import Offer
from src.offers.offer_service import OfferService, PermissionDeniedError


class ConfigRepoStub(ConfigRepoPort):
    """Stub: ConfigRepoPort with hardcoded test values."""

    server_host: str = "localhost"
    server_port: int = 8888
    issuer_agent_base_url: str = "https://issuer-agent.example.com"
    public_url: str = "http://localhost:8888"
    debug: bool = False


class AccessControlStub(AccessControlPort):
    """Stub: always grants any permission request."""

    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        """Always return True."""
        return True


class DenyingAccessControlStub(AccessControlPort):
    """Stub: always denies any permission request."""

    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        """Always return False."""
        return False


class IssuerAgentStub(IssuerAgentPort):
    """Stub: returns hardcoded credential issuer metadata; no-ops create_offer."""

    credential_issuer: str
    credential_endpoint: str
    credential_configurations_supported: dict[str, CredentialConfiguration]  # noqa: E501
    authorization_servers: list[str] | None

    def __init__(
        self,
        credential_issuer: str = "https://issuer.example.com",
        credential_endpoint: str = "https://example.com/credential",
        credential_configurations_supported: dict[str, CredentialConfiguration]
        | None = None,
        authorization_servers: list[str] | None = None,
    ) -> None:
        """Initialize with configurable metadata.

        Args:
            credential_issuer: The credential issuer URL.
            credential_endpoint: The credential endpoint URL.
            credential_configurations_supported: The credential configurations.
            authorization_servers: The authorization servers.
        """
        self.credential_issuer = credential_issuer
        self.credential_endpoint = credential_endpoint
        self.credential_configurations_supported = (
            credential_configurations_supported or {}
        )
        self.authorization_servers = authorization_servers

    @override
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Return hardcoded metadata."""
        return CredentialIssuerMetadata(
            credential_issuer=self.credential_issuer,
            credential_endpoint=self.credential_endpoint,
            credential_configurations_supported=self.credential_configurations_supported,
            authorization_servers=self.authorization_servers,
        )

    @override
    def create_offer(self, offer_id: str, achievement_id: str) -> None:
        """No-op stub."""

    @override
    def credential_request(
        self,
        format: str,
        credential_configuration_id: str,
        proof: dict[str, object],
        issuer_state: str,
        access_token: str,
    ) -> CredentialResponse:
        """No-op stub that raises NotImplementedError."""
        raise NotImplementedError


class IssuerAgentSpy(IssuerAgentPort):
    """Spy: records create_offer calls; no-ops the actual operation."""

    offers: list[tuple[str, str]]

    def __init__(self) -> None:
        """Initialise with empty call log."""
        self.offers = []

    @override
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Not needed in offer tests."""
        raise NotImplementedError

    @override
    def create_offer(self, offer_id: str, achievement_id: str) -> None:
        """Record the call."""
        self.offers.append((offer_id, achievement_id))

    @override
    def credential_request(
        self,
        format: str,
        credential_configuration_id: str,
        proof: dict[str, object],
        issuer_state: str,
        access_token: str,
    ) -> CredentialResponse:
        """Not needed in offer tests."""
        raise NotImplementedError


class MetadataServiceStub(MetadataService):
    """Stub: MetadataService backed by IssuerAgentStub."""

    def __init__(self, public_url: str = "http://localhost:8888") -> None:
        """Initialise with stub issuer agent.

        Args:
            public_url: The public URL to use for the metadata.
        """
        super().__init__(issuer_agent=IssuerAgentStub(), public_url=public_url)


class DenyingOfferServiceStub(OfferService):
    """Stub: always raises PermissionDeniedError from create_offer."""

    def __init__(self) -> None:
        """Initialise with stub dependencies."""
        super().__init__(
            issuer_agent=IssuerAgentStub(),
            access_control=DenyingAccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url="http://localhost:8888",
        )

    @override
    def create_offer(self, achievement_id: str, bearer_token: str) -> Offer:
        """Always raise PermissionDeniedError."""
        raise PermissionDeniedError(achievement_id)


class OfferServiceSpy(OfferService):
    """Spy: records create_offer calls and delegates to the real OfferService."""

    calls: list[tuple[str, str, str]]

    def __init__(self, public_url: str = "http://localhost:8888") -> None:
        """Initialise with stub dependencies and an empty call log.

        Args:
            public_url: Issuer public URL used for offer URI construction.
        """
        self.calls = []
        super().__init__(
            issuer_agent=IssuerAgentStub(),
            access_control=AccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url=public_url,
        )

    @override
    def create_offer(self, achievement_id: str, bearer_token: str) -> Offer:
        """Record call then delegate to the real implementation.

        Args:
            achievement_id: The achievement identifier.
            bearer_token: The caller's bearer token.

        Returns:
            The created Offer.
        """
        self.calls.append(("create_offer", achievement_id, bearer_token))
        return super().create_offer(achievement_id, bearer_token)
