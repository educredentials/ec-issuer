"""Offer service for creating and retrieving credential offers."""

import uuid

from src.access_control.access_control_port import AccessControlPort
from src.awards.award_service import AwardService
from src.awards.awards_client_port import (
    AwardForbidden,
    AwardNotFound,
    AwardsClientError,
)

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
    _offers_client: OffersClientPort
    _offers_repository: OffersRepositoryPort
    _award_service: AwardService

    def __init__(
        self,
        access_control: AccessControlPort,
        offers_client: OffersClientPort,
        offers_repository: OffersRepositoryPort,
        award_service: AwardService,
    ) -> None:
        """Initialise the service with its dependencies.

        Args:
            access_control: Adapter for checking resource permissions.
            offers_repository: Adapter for persisting offers.
            offers_client: Adapter for interacting with oid4vci agent.
            award_service: Service for fetching awards.
        """
        self._access_control = access_control
        self._offers_client = offers_client
        self._offers_repository = offers_repository
        self._award_service = award_service

    def create_offer(self, award_id: str, bearer_token: str) -> Offer:
        """Create, persist, and return a new credential offer.

        Args:
            award_id: The award/achievement to issue.
            bearer_token: The caller's bearer token used for permission checking.

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
            award = self._award_service.get(award_id)
        except AwardNotFound:
            raise NotFoundError(f"Award {award_id} not found")
        except AwardForbidden:
            raise PermissionDeniedError(award_id)
        except AwardsClientError as e:
            raise OfferServiceError(str(e)) from e

        offer_id = str(uuid.uuid4())

        # TODO: wrap in transaction
        uri = self._offers_client.create(offer_id, award)
        offer = Offer(offer_id=offer_id, award_id=award_id, uri=uri)
        self._offers_repository.store(offer)

        return offer

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
        except OfferNotFound:
            raise NotFoundError(f"Offer {offer_id} not found")
        except OffersClientError as e:
            raise OfferServiceError(str(e)) from e

        try:
            stored_offer = self._offers_repository.get(offer_id)
        except KeyError:
            raise NotFoundError(f"Offer {offer_id} not found")

        return Offer(
            offer_id=offer_id,
            award_id=stored_offer.award_id,
            uri=upstream_offer.uri,
        )
