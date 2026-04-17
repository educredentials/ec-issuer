"""Offer service for creating and retrieving credential offers."""

import uuid

from src.access_control.access_control_port import AccessControlPort
from src.issuer_agent.issuer_agent_port import IssuerAgentPort
from src.offers.offer_repository import Offer, OffersRepositoryPort


class PermissionDeniedError(Exception):
    """Raised when access control denies the requested action."""


class OfferService:
    """Service that orchestrates offer creation."""

    _issuer_agent: IssuerAgentPort
    _access_control: AccessControlPort
    _offers_repository: OffersRepositoryPort
    _public_url: str

    def __init__(
        self,
        issuer_agent: IssuerAgentPort,
        access_control: AccessControlPort,
        offers_repository: OffersRepositoryPort,
        public_url: str,
    ) -> None:
        """Initialise the service with its dependencies.

        Args:
            issuer_agent: Adapter for the SSI agent that registers the offer.
            access_control: Adapter for checking resource permissions.
            offers_repository: Adapter for persisting offers.
            public_url: Publicly accessible base URL of this issuer service,
                used to build the offer URI.
        """
        self._issuer_agent = issuer_agent
        self._access_control = access_control
        self._offers_repository = offers_repository
        self._public_url = public_url

    def create_offer(self, achievement_id: str, bearer_token: str) -> Offer:
        """Create, persist, and return a new credential offer.

        Args:
            achievement_id: The award/achievement to issue.
            bearer_token: The caller's bearer token used for permission checking.

        Returns:
            The newly created Offer.

        Raises:
            PermissionDeniedError: When the caller is not permitted to import the award.
        """
        if not self._access_control.may_import(
            bearer_token, achievement_id, "Award", "import"
        ):
            raise PermissionDeniedError(achievement_id)

        offer_id = str(uuid.uuid4())
        self._issuer_agent.create_offer(offer_id, achievement_id)

        uri = f"openid-credential-offer://?credential_offer_uri={self._public_url}/api/v1/offers/{offer_id}"
        offer = Offer(
            offer_id=offer_id,
            achievement_id=achievement_id,
            uri=uri,
            credential_issuer=self._public_url,
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
        return self._offers_repository.get(offer_id)
