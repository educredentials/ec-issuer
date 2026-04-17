"""Domain model and port for the offers repository."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Offer:
    """Domain model representing a credential offer."""

    offer_id: str
    achievement_id: str
    uri: str
    credential_issuer: str

    def to_credential_offer(self) -> dict[str, object]:
        """Return the credential offer structure as defined by the OID4VCI spec.

        Returns:
            A dict with credential_issuer, credential_configuration_ids, and grants.
        """
        return {
            "credential_issuer": self.credential_issuer,
            "credential_configuration_ids": ["UniversityDegreeCredential"],
            "grants": {
                "authorization_code": {
                    "issuer_state": self.offer_id,
                }
            },
        }


class OffersRepositoryPort(ABC):
    """Port: repository interface for persisting and retrieving offers."""

    @abstractmethod
    def store(self, offer: Offer) -> None:
        """Persist an offer.

        Args:
            offer: The offer to store.
        """
        ...

    @abstractmethod
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            KeyError: When no offer with the given id exists.
        """
        ...
