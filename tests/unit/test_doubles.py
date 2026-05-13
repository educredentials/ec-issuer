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
from src.metadata.metadata_repository import (
    MetadataNotFoundError,
    MetadataRepositoryPort,
)
from src.metadata.metadata_service import MetadataService
from src.offers.models import Offer
from src.offers.offer_service import (
    DoesNotExistInClientError,
    DoesNotExistInRepositoryError,
    OfferService,
    PermissionDeniedError,
)
from src.offers.offers_client_port import OffersClientPort
from src.offers.offers_repository_port import OffersRepositoryPort


class OffersClientStub(OffersClientPort):
    @override
    def create(self, offer_id: str) -> str:
        """Persist an offer in memory.

        Args:
            offer_id: The id of the offer to create on the agent

        Returns:
            The offer uri
        """

        return f"openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/{offer_id}"

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            KeyError: When no offer with the given id exists.
        """
        return Offer(
            offer_id=offer_id,
            award_id="award-345",
            uri=f"openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/{offer_id}",
        )


class OffersClientStubNotFound(OffersClientStub):
    @override
    def get(self, offer_id: str) -> Offer:
        raise DoesNotExistInClientError


class OffersClientSpy(OffersClientPort):
    """Spy: OffersClientPort that records all calls."""

    def __init__(self) -> None:
        self._calls: list[tuple[str, dict[str, str]]] = []

    @property
    def calls(self) -> list[tuple[str, dict[str, str]]]:
        """Return all calls made to this spy."""
        return self._calls

    @override
    def create(self, offer_id: str) -> str:
        """Create a new offer for the given achievement.

        Args:
            award_id: The achievement identifier.

        Returns:
            The newly created offer.
        """
        self._calls.append(("create", {"offer_id": offer_id}))

        return f"openid-credential-offer://?credential_offer_uri=https://issuer-agent.example.com/credential_offer/{offer_id}"

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            KeyError: When no offer with the given id exists.
        """
        self._calls.append(("get", {"offer_id": offer_id}))  # type: ignore[func-returns-value]

        return Offer(
            offer_id=offer_id,
            award_id="achievement-1234",
            uri=f"openid-credential-offer://?credential_offer_uri=https://issuer-agent.example.com/credential_offer/{offer_id}",
        )


class OffersRepositoryStub(OffersRepositoryPort):
    @override
    def store(self, offer: Offer) -> None:
        pass

    @override
    def get(self, offer_id: str) -> Offer:
        return Offer(offer_id=offer_id, award_id="award-123", uri=None)


class OffersRepositoryStubNotFound(OffersRepositoryStub):
    @override
    def get(self, offer_id: str) -> Offer:
        raise DoesNotExistInRepositoryError


class OffersRepositorySpy(OffersRepositoryPort):
    def __init__(self) -> None:
        self._calls: list[tuple[str, dict[str, str | Offer]]] = []

    @property
    def calls(self) -> list[tuple[str, dict[str, str | Offer]]]:
        """Return all calls made to this spy."""
        return self._calls

    @override
    def store(self, offer: Offer) -> None:
        self._calls.append(("store", {"offer": offer}))

    @override
    def get(self, offer_id: str) -> Offer:
        self._calls.append(("get", {"offer_id": offer_id}))
        return Offer(
            offer_id=offer_id,
            award_id="achievement-1234",
            uri=f"openid-credential-offer://?credential_offer_uri=https://issuer-agent.example.com/credential_offer/{offer_id}",
        )


class ConfigRepoStub(ConfigRepoPort):
    """Stub: ConfigRepoPort with hardcoded test values."""

    server_host: str = "localhost"
    server_port: int = 8888
    ssi_agent_url: str = "https://issuer-agent.example.com"
    ssi_agent_nonce_endpoint: str = "https://issuer-agent.example.com/openid4vci/nonce"
    ssi_agent_credential_endpoint: str = (
        "https://issuer-agent.example.com/openid4vci/credential"
    )
    public_url: str = "http://localhost:8888"
    debug: bool = False
    postgresql_connection_string: str = "postgresql://test:test@localhost:5432/test"


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


class AccessControlSpy(AccessControlPort):
    """Spy: records calls to may_import."""

    calls: list[tuple[str, str, str, str]]

    def __init__(self) -> None:
        """Initialise with empty call log."""
        self.calls = []

    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        """Record the call and grant permission."""
        self.calls.append((bearer_token, resource_id, resource_type, permission))
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
    nonce_endpoint: str | None
    credential_configurations_supported: dict[str, CredentialConfiguration]  # noqa: E501
    authorization_servers: list[str] | None

    def __init__(
        self,
        credential_issuer: str = "https://issuer.example.com",
        credential_endpoint: str = "https://issuer.example.com/credential",
        nonce_endpoint: str = "https://issuer.example.com/nonce",
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
        self.nonce_endpoint = nonce_endpoint
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
            nonce_endpoint=self.nonce_endpoint,
            credential_configurations_supported=self.credential_configurations_supported,
            authorization_servers=self.authorization_servers,
        )

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

    @override
    def request_nonce(self) -> dict[str, str]:
        """Return a hardcoded nonce response."""
        return {"c_nonce": "wKI4LT17ac15ES9bw8ac4"}


class DenyingOfferServiceStub(OfferService):
    """Stub: always raises PermissionDeniedError from create_offer."""

    def __init__(self) -> None:
        """Initialise with stub dependencies."""
        super().__init__(
            access_control=DenyingAccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
        )

    @override
    def create_offer(self, award_id: str, bearer_token: str) -> Offer:
        """Always raise PermissionDeniedError."""
        raise PermissionDeniedError(award_id)


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
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
        )

    @override
    def create_offer(self, award_id: str, bearer_token: str) -> Offer:
        """Record call then delegate to the real implementation.

        Args:
            award_id: The achievement identifier.
            bearer_token: The caller's bearer token.

        Returns:
            The created Offer.
        """
        self.calls.append(("create_offer", award_id, bearer_token))
        return super().create_offer(award_id, bearer_token)


class InMemoryMetadataRepositoryStub(MetadataRepositoryPort):
    """Stub: In-memory repository for metadata, for use in unit tests only."""

    def __init__(self) -> None:
        """Initialise with an empty store."""
        self._store: list[CredentialIssuerMetadata] = []

    @override
    def store(self, metadata: CredentialIssuerMetadata) -> None:
        """Persist metadata in memory.

        Args:
            metadata: The CredentialIssuerMetadata to store.
        """
        self._store.append(metadata)

    @override
    def get(self) -> CredentialIssuerMetadata:
        """Retrieve the latest metadata entry.

        Returns:
            The latest CredentialIssuerMetadata.

        Raises:
            MetadataNotFoundError: When no metadata entry exists.
        """
        if not self._store:
            raise MetadataNotFoundError("No metadata entry found")
        return self._store[-1]


class MetadataServiceStub(MetadataService):
    """Stub: MetadataService backed by InMemoryMetadataRepositoryStub."""

    def __init__(self, public_url: str = "http://localhost:8888") -> None:
        """Initialise with stub metadata repository.

        Args:
            public_url: The public URL to use for the metadata.
        """
        super().__init__(
            metadata_repository=InMemoryMetadataRepositoryStub(), public_url=public_url
        )
