"""Shared test doubles for unit tests.

See docs/src/test_doubles.md for naming conventions and rules.
"""

from typing import override

from src.access_control.access_control_port import AccessControlPort
from src.awards.award_service import AwardService
from src.awards.awards_client_port import AwardsClientPort
from src.awards.models import (
    Achievement,
    AchievementSubject,
    Award,
    Criteria,
    Issuer,
)
from src.config.config_port import ConfigRepoPort

from src.offers.models import Offer
from src.offers.offer_service import (
    OfferService,
    PermissionDeniedError,
)
from src.offers.offers_client_port import OfferNotFound, OffersClientPort
from src.offers.offers_repository_port import OffersRepositoryPort

# A fixed Award returned by AwardServiceStub and _AwardsClientStub.
# Tests that need to assert on the exact award being passed can import this.
STUB_AWARD: Award = Award(
    id="http://example.com/awards/stub-award",
    type=["VerifiableCredential", "OpenBadgeCredential"],
    name="Stub Award",
    issuer=Issuer(
        id="http://example.com/issuers/stub",
        type=["Profile"],
        name="Stub Issuer",
    ),
    validFrom="2024-01-01T00:00:00Z",
    credentialSubject=AchievementSubject(
        id="did:example:stub-subject",
        type=["AchievementSubject"],
        achievement=Achievement(
            id="http://example.com/achievements/stub",
            type=["Achievement"],
            criteria=Criteria(narrative="Stub criteria narrative."),
            description="Stub achievement description.",
            name="Stub Achievement",
        ),
    ),
)


class _AwardsClientStub(AwardsClientPort):
    """Private stub: always returns STUB_AWARD."""

    @override
    def get(self, award_id: str) -> Award:
        """Return the shared STUB_AWARD.

        Args:
            award_id: Ignored.

        Returns:
            STUB_AWARD.
        """
        return STUB_AWARD


class AwardServiceStub(AwardService):
    """Stub: AwardService that always returns STUB_AWARD."""

    def __init__(self) -> None:
        """Initialise with a stub client."""
        super().__init__(client=_AwardsClientStub())


class OffersClientStub(OffersClientPort):
    """Stub: OffersClientPort that returns fixed offers."""

    @override
    def create(self, offer_id: str, award: Award) -> str:
        """Return a stub offer URI.

        Args:
            offer_id: The offer identifier.
            award: Ignored.

        Returns:
            A stub offer URI.
        """
        return f"openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/{offer_id}"

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve a stub offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.
        """
        return Offer(
            offer_id=offer_id,
            award_id="award-345",
            uri=f"openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/{offer_id}",
        )


class OffersClientStubNotFound(OffersClientStub):
    """Stub: get() always raises OfferNotFound (missing offer in the client)."""

    @override
    def get(self, offer_id: str) -> Offer:
        """Raise OfferNotFound.

        Args:
            offer_id: The identifier that was not found.

        Raises:
            OfferNotFound: Always.
        """
        raise OfferNotFound(f"Offer {offer_id} not found")


class OffersClientSpy(OffersClientPort):
    """Spy: OffersClientPort that records all calls."""

    def __init__(self) -> None:
        """Initialise with empty call log."""
        self._calls: list[tuple[str, dict[str, object]]] = []

    @property
    def calls(self) -> list[tuple[str, dict[str, object]]]:
        """Return all calls made to this spy.

        Returns:
            A list of recorded call tuples.
        """
        return self._calls

    @override
    def create(self, offer_id: str, award: Award) -> str:
        """Record the call and return a stub URI.

        Args:
            offer_id: The offer identifier.
            award: The award passed to create.

        Returns:
            A stub offer URI.
        """
        self._calls.append(("create", {"offer_id": offer_id, "award": award}))
        return f"openid-credential-offer://?credential_offer_uri=https://issuer-agent.example.com/credential_offer/{offer_id}"

    @override
    def get(self, offer_id: str) -> Offer:
        """Record the call and return a stub Offer.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            A stub Offer.
        """
        self._calls.append(("get", {"offer_id": offer_id}))  # type: ignore[func-returns-value]

        return Offer(
            offer_id=offer_id,
            award_id="achievement-1234",
            uri=f"openid-credential-offer://?credential_offer_uri=https://issuer-agent.example.com/credential_offer/{offer_id}",
        )


class OffersRepositoryStub(OffersRepositoryPort):
    """Stub: OffersRepositoryPort with in-memory behaviour."""

    @override
    def store(self, offer: Offer) -> None:
        """No-op store.

        Args:
            offer: Ignored.
        """
        pass

    @override
    def get(self, offer_id: str) -> Offer:
        """Return a stub Offer.

        Args:
            offer_id: The offer identifier.

        Returns:
            A stub Offer with award_id='award-123'.
        """
        return Offer(offer_id=offer_id, award_id="award-123", uri=None)


class OffersRepositoryStubNotFound(OffersRepositoryStub):
    """Stub: get() always raises KeyError (missing offer in the repository)."""

    @override
    def get(self, offer_id: str) -> Offer:
        """Raise KeyError.

        Args:
            offer_id: The identifier that was not found.

        Raises:
            KeyError: Always.
        """
        raise KeyError(offer_id)


class OffersRepositorySpy(OffersRepositoryPort):
    """Spy: records all calls."""

    def __init__(self) -> None:
        """Initialise with empty call log."""
        self._calls: list[tuple[str, dict[str, str | Offer]]] = []

    @property
    def calls(self) -> list[tuple[str, dict[str, str | Offer]]]:
        """Return all calls made to this spy.

        Returns:
            A list of recorded call tuples.
        """
        return self._calls

    @override
    def store(self, offer: Offer) -> None:
        """Record the store call.

        Args:
            offer: The offer that was stored.
        """
        self._calls.append(("store", {"offer": offer}))

    @override
    def get(self, offer_id: str) -> Offer:
        """Record the get call and return a stub Offer.

        Args:
            offer_id: The offer identifier.

        Returns:
            A stub Offer.
        """
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
    debug: bool = False
    postgresql_connection_string: str = "postgresql://test:test@localhost:5432/test"
    awards_service_url: str = "http://awards.example.com"
    allowed_cors_domains: str = "http://localhost:8000,https://app.example.com"


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
        """Always return True.

        Args:
            bearer_token: Ignored.
            resource_id: Ignored.
            resource_type: Ignored.
            permission: Ignored.

        Returns:
            True.
        """
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
        """Record the call and grant permission.

        Args:
            bearer_token: The bearer token.
            resource_id: The resource identifier.
            resource_type: The resource type.
            permission: The permission being checked.

        Returns:
            True.
        """
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
        """Always return False.

        Args:
            bearer_token: Ignored.
            resource_id: Ignored.
            resource_type: Ignored.
            permission: Ignored.

        Returns:
            False.
        """
        return False


class DenyingOfferServiceStub(OfferService):
    """Stub: always raises PermissionDeniedError from create_offer."""

    def __init__(self) -> None:
        """Initialise with stub dependencies."""
        super().__init__(
            access_control=DenyingAccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            award_service=AwardServiceStub(),
        )

    @override
    def create_offer(self, award_id: str, bearer_token: str) -> Offer:
        """Always raise PermissionDeniedError.

        Args:
            award_id: Ignored.
            bearer_token: Ignored.

        Raises:
            PermissionDeniedError: Always.
        """
        raise PermissionDeniedError(award_id)


class OfferServiceSpy(OfferService):
    """Spy: records create_offer calls and delegates to the real OfferService."""

    calls: list[tuple[str, str, str]]

    def __init__(self) -> None:
        """Initialise with stub dependencies and an empty call log."""
        self.calls = []
        super().__init__(
            access_control=AccessControlStub(),
            offers_repository=OffersRepositoryStub(),
            offers_client=OffersClientStub(),
            award_service=AwardServiceStub(),
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
