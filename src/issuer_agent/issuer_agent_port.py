"""Issuer Agent Port module."""

from abc import ABC, abstractmethod

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata

class MetadataError(Exception):
    """Exception raised when there is an error in the metadata."""

    pass

class IssuerAgentPort(ABC):
    """Port for Issuer Agent Adapters."""

    @abstractmethod
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Return Credential Issuer Metadata.

        Returns:
            CredentialIssuerMetadata object.
        """
        ...

    @abstractmethod
    def create_offer(self, offer_id: str, achievement_id: str) -> None:
        """Create an offer in the issuer agent.

        Args:
            offer_id: The unique identifier for the offer.
            achievement_id: The achievement/award identifier to issue.
        """
        ...
