"""Offer service for creating and retrieving credential offers."""

import uuid

from src.access_control.access_control_port import AccessControlPort
from src.offers.models import Offer
from src.offers.offers_client_port import OffersClientPort
from src.offers.offers_repository_port import OffersRepositoryPort


class PermissionDeniedError(Exception):
    """Raised when access control denies the requested action."""

class DoesNotExistInRepositoryError(Exception):
    """Raised when offer cannot be found in Repository"""

class DoesNotExistInClientError(Exception):
    """Raised when offer cannot be found in API"""

class OfferService:
    """Service that orchestrates offer creation."""

    _access_control: AccessControlPort
    _offers_client: OffersClientPort
    _offers_repository: OffersRepositoryPort

    def __init__(
        self,
        access_control: AccessControlPort,
        offers_client: OffersClientPort,
        offers_repository: OffersRepositoryPort,
    ) -> None:
        """Initialise the service with its dependencies.

        Args:
            access_control: Adapter for checking resource permissions.
            offers_repository: Adapter for persisting offers.
            offers_client: Adapter for interacting with oid4vci agent.
            public_url: Publicly accessible base URL of this issuer service,
                used to build the offer URI.
        """
        self._access_control = access_control
        self._offers_client = offers_client
        self._offers_repository = offers_repository

    def create_offer(self, award_id: str, bearer_token: str) -> Offer:
        """Create, persist, and return a new credential offer.

        Args:
            award_id: The award/achievement to issue.
            bearer_token: The caller's bearer token used for permission checking.

        Returns:
            The newly created Offer.

        Raises:
            PermissionDeniedError: When the caller is not permitted to import the award.
        """
        if not self._access_control.may_import(
            bearer_token, award_id, "Award", "import"
        ):
            raise PermissionDeniedError(award_id)

        offer_id = str(uuid.uuid4())
        # award: Award = Award()  # TODO: Get the actual award from where?

        # TODO: wrap in transaction
        uri = self._offers_client.create(offer_id)
        offer = Offer(
            offer_id = offer_id,
            award_id = award_id,
            uri = uri
        )
        self._offers_repository.store(offer)

        return offer


    def get_offer(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            KeyError: When no offer with the given id exists.
        """

        upstream_offer = self._offers_client.get(offer_id)
        stored_offer = self._offers_repository.get(offer_id)
        return Offer(
            offer_id = offer_id,
            award_id = stored_offer.award_id,
            uri = upstream_offer.uri,
        )
