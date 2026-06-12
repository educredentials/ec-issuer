"""Integration tests: OfferService + AwardService interaction.

Real modules wired together; AwardsClientPort and OffersClientPort
are replaced with in-test doubles to avoid HTTP calls.
"""

from typing import override

import pytest

from src.access_control.access_control_port import AccessControlPort
from src.awards.award_service import AwardService
from src.awards.awards_client_port import (
    AwardForbidden,
    AwardNotFound,
    AwardsClientError,
    AwardsClientPort,
)
from src.awards.models import (
    Achievement,
    AchievementSubject,
    Award,
    Criteria,
    Issuer,
)
from src.offers.models import Offer
from src.offers.offer_service import (
    NotFoundError,
    OfferService,
    OfferServiceError,
    PermissionDeniedError,
)
from src.offers.offers_client_port import OffersClientPort
from src.offers.offers_repository_port import OffersRepositoryPort


class _AllowingAccessControl(AccessControlPort):
    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        return True


class _OffersRepositoryStub(OffersRepositoryPort):
    @override
    def store(self, offer: Offer) -> None:
        pass

    @override
    def get(self, offer_id: str) -> Offer:
        return Offer(offer_id=offer_id, award_id="", uri=None)


class _OffersClientSpy(OffersClientPort):
    """Records all calls to create() for assertion."""

    def __init__(self) -> None:
        """Initialise with empty call log."""
        self.calls: list[tuple[str, dict[str, object]]] = []

    @override
    def create(self, offer_id: str, award: Award) -> str:
        """Record the call and return a stub URI.

        Args:
            offer_id: The offer identifier.
            award: The award passed to the client.

        Returns:
            A stub offer URI.
        """
        self.calls.append(("create", {"offer_id": offer_id, "award": award}))
        return f"openid-credential-offer://?credential_offer_uri=http://example.com/offers/{offer_id}"

    @override
    def get(self, offer_id: str) -> Offer:
        """Return a stub offer.

        Args:
            offer_id: The offer identifier.

        Returns:
            A stub Offer.
        """
        return Offer(offer_id=offer_id, award_id="", uri=None)


class _AwardsClientStub(AwardsClientPort):
    """Stub that always returns the configured Award."""

    def __init__(self, award: Award) -> None:
        """Initialise with the Award to return.

        Args:
            award: The award to return from get().
        """
        self._award: Award = award

    @override
    def get(self, award_id: str) -> Award:
        """Return the configured Award.

        Args:
            award_id: Ignored.

        Returns:
            The configured Award.
        """
        return self._award


class _AwardsClientNotFoundStub(AwardsClientPort):
    """Stub that always raises AwardNotFound."""

    @override
    def get(self, award_id: str) -> Award:
        """Raise AwardNotFound.

        Args:
            award_id: The identifier that was not found.

        Raises:
            AwardNotFound: Always.
        """
        raise AwardNotFound(award_id)


class _AwardsClientForbiddenStub(AwardsClientPort):
    """Stub that always raises AwardForbidden."""

    @override
    def get(self, award_id: str) -> Award:
        """Raise AwardForbidden.

        Args:
            award_id: The identifier for which access is denied.

        Raises:
            AwardForbidden: Always.
        """
        raise AwardForbidden(award_id)


class _AwardsClientErrorStub(AwardsClientPort):
    """Stub that always raises AwardsClientError."""

    @override
    def get(self, award_id: str) -> Award:
        """Raise AwardsClientError.

        Args:
            award_id: The identifier (unused).

        Raises:
            AwardsClientError: Always.
        """
        raise AwardsClientError("upstream service unavailable")


@pytest.fixture
def sample_award() -> Award:
    """Provide a minimal valid OB3 AchievementCredential Award."""
    return Award(
        id="http://example.com/credentials/3527",
        type=["VerifiableCredential", "OpenBadgeCredential"],
        name="Teamwork Badge",
        issuer=Issuer(
            id="https://example.com/issuers/876543",
            type=["Profile"],
            name="Example Corp",
        ),
        validFrom="2010-01-01T00:00:00Z",
        credentialSubject=AchievementSubject(
            id="did:example:ebfeb1f712ebc6f1c276e12ec21",
            type=["AchievementSubject"],
            achievement=Achievement(
                id="https://example.com/achievements/21st-century-skills/teamwork",
                type=["Achievement"],
                criteria=Criteria(
                    narrative=(
                        "Team members are nominated for this badge by their peers."
                    )
                ),
                description=(
                    "This badge recognizes the capacity to collaborate in a group."
                ),
                name="Teamwork",
            ),
        ),
    )


class TestOfferAwardsServiceInteraction:
    """Integration tests for the interaction between OfferService and AwardService."""

    def test_create_offer_fetches_award_and_passes_it_to_offers_client(
        self, sample_award: Award
    ) -> None:
        """create_offer fetches award via AwardService and passes it to offers client.

        Tracer bullet: verifies the full interaction path.
        """
        offers_client = _OffersClientSpy()
        award_service = AwardService(client=_AwardsClientStub(award=sample_award))
        service = OfferService(
            access_control=_AllowingAccessControl(),
            offers_repository=_OffersRepositoryStub(),
            offers_client=offers_client,
            award_service=award_service,
        )

        offer = service.create_offer(award_id="award-123", bearer_token="tok")

        assert len(offers_client.calls) == 1
        call_name, call_args = offers_client.calls[0]
        assert call_name == "create"
        assert call_args["offer_id"] == offer.offer_id
        assert call_args["award"] == sample_award

    def test_create_offer_raises_award_not_found_when_award_service_returns_not_found(
        self,
    ) -> None:
        """create_offer raises AwardNotFoundError when the award does not exist."""
        service = OfferService(
            access_control=_AllowingAccessControl(),
            offers_repository=_OffersRepositoryStub(),
            offers_client=_OffersClientSpy(),
            award_service=AwardService(client=_AwardsClientNotFoundStub()),
        )

        with pytest.raises(NotFoundError, match="Award unknown-award not found"):
            _ = service.create_offer(award_id="unknown-award", bearer_token="tok")

    def test_create_offer_raises_permission_denied_when_award_service_returns_forbidden(
        self,
    ) -> None:
        """create_offer raises PermissionDeniedError on AwardForbidden."""
        service = OfferService(
            access_control=_AllowingAccessControl(),
            offers_repository=_OffersRepositoryStub(),
            offers_client=_OffersClientSpy(),
            award_service=AwardService(client=_AwardsClientForbiddenStub()),
        )

        with pytest.raises(PermissionDeniedError):
            _ = service.create_offer(award_id="forbidden-award", bearer_token="tok")

    def test_create_offer_raises_awards_service_error_when_awards_client_fails(
        self,
    ) -> None:
        """create_offer raises AwardsServiceError on AwardsClientError."""
        service = OfferService(
            access_control=_AllowingAccessControl(),
            offers_repository=_OffersRepositoryStub(),
            offers_client=_OffersClientSpy(),
            award_service=AwardService(client=_AwardsClientErrorStub()),
        )

        with pytest.raises(OfferServiceError):
            _ = service.create_offer(award_id="award-123", bearer_token="tok")
