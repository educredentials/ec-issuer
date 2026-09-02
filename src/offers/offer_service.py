"""Offer service for creating and retrieving credential offers."""

import uuid

from src.access_control.access_control_port import AccessControlPort
from src.awards.awards_client_port import (
    AwardForbidden,
    AwardNotFound,
    AwardsClientError,
    AwardsClientPort,
)
from src.awards.models import EDCAward, OB3Award

from .models import Offer
from .offers_client_port import OfferNotFound, OffersClientError, OffersClientPort
from .offers_repository_port import OffersRepositoryPort


class PermissionDeniedError(Exception):
    """Raised when access control denies the requested action."""


class NotFoundError(Exception):
    """Raised when a requested resource cannot be found.

    The message includes the resource type and identifier so that developers
    and operators can pinpoint the source, e.g. "Award award-42 not found"
    or "Offer offer-7 not found".
    """


class OfferServiceError(Exception):
    """Raised when an upstream service returns an unexpected error.

    Wraps the original exception message so that the cause is preserved
    for logging and debugging.
    """


class OfferService:
    """Service that orchestrates offer creation."""

    _access_control: AccessControlPort
    _awards_client: AwardsClientPort
    _offers_repository: OffersRepositoryPort
    _offers_client: OffersClientPort

    def __init__(
        self,
        access_control: AccessControlPort,
        awards_client: AwardsClientPort,
        offers_repository: OffersRepositoryPort,
        offers_client: OffersClientPort,
    ) -> None:
        """Initialise the service with its dependencies.

        Args:
            access_control: Adapter for checking resource permissions.
            awards_client: Adapter for fetching awards from the external awards service.
            offers_repository: Adapter for persisting offers.
            offers_client: Adapter for interacting with oid4vci agent.
        """
        self._access_control = access_control
        self._awards_client = awards_client
        self._offers_repository = offers_repository
        self._offers_client = offers_client

    def create_offer(
        self,
        award_id: str,
        bearer_token: str,
        *,
        credential_type: str = "ob3",
    ) -> Offer:
        """Create, persist, and return a new credential offer.

        Args:
            award_id: The award/achievement to issue.
            bearer_token: The caller's bearer token used for permission checking.
            credential_type: The credential type to issue — ``"ob3"`` (default) or
                ``"edc"``.

        Returns:
            The newly created Offer.

        Raises:
            PermissionDeniedError: When the caller is not permitted to import the award,
                or when the awards service denies access.
            NotFoundError: When the award does not exist in the awards service.
            OfferServiceError: When an upstream service returns an unexpected error.
        """
        if not self._access_control.may_import(
            bearer_token, award_id, "Award", "import"
        ):
            raise PermissionDeniedError(award_id)

        try:
            award = self._awards_client.get(award_id, bearer_token)
        except AwardNotFound as e:
            raise NotFoundError(f"Award {award_id} not found") from e
        except AwardForbidden as e:
            raise PermissionDeniedError(award_id) from e
        except AwardsClientError as e:
            raise OfferServiceError(str(e)) from e

        offer_id = str(uuid.uuid4())

        # TODO: wrap in transaction
        uri = self._dispatch_create_offer(offer_id, award, credential_type)
        offer = Offer(offer_id=offer_id, award_id=award_id, uri=uri)
        self._offers_repository.store(offer)

        return offer

    def _dispatch_create_offer(
        self,
        offer_id: str,
        award: OB3Award,
        credential_type: str,
    ) -> str:
        """Dispatch offer creation to the correct client method.

        Args:
            offer_id: The offer identifier.
            award: The OB3 award fetched from the awards service.
            credential_type: The target credential type.

        Returns:
            The offer URI from the SSI agent.
        """
        if credential_type == "edc":
            edc_award = self._ob3_to_edc(award)
            return self._offers_client.create_edc(offer_id, edc_award)

        return self._offers_client.create_ob3(offer_id, award)

    @staticmethod
    def _ob3_to_edc(award: OB3Award) -> EDCAward:
        """Map an OB3 award to an EDC claim set.

        Only the name is mapped from the OB3 award; person and body data
        use placeholder values until the awards service exposes them.

        Args:
            award: The OB3 AchievementCredential.

        Returns:
            An EDC claim set ready for SD-JWT issuance.
        """
        return EDCAward(
            given_name="Learner",
            family_name="Example",
            learning_achievement={
                "name": award.credentialSubject.achievement.name,
                "description": award.credentialSubject.achievement.description,
                "type": "achievement",
            },
            awarding_body={
                "name": award.issuer.name,
                "id": award.issuer.id,
            },
            awarding_opportunity={
                "name": award.name,
            },
        )

    def get_offer(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            NotFoundError: When the offer cannot be found in the client or repository.
            OfferServiceError: When the upstream client returns an unexpected error.
        """
        try:
            upstream_offer = self._offers_client.get(offer_id)
        except OfferNotFound as e:
            raise NotFoundError(f"Offer {offer_id} not found") from e
        except OffersClientError as e:
            raise OfferServiceError(str(e)) from e

        try:
            stored_offer = self._offers_repository.get(offer_id)
        except KeyError as e:
            raise NotFoundError(f"Offer {offer_id} not found") from e

        return Offer(
            offer_id=offer_id,
            award_id=stored_offer.award_id,
            uri=upstream_offer.uri,
        )
