"""Sysadmin port defining the administrative operations interface."""

from abc import ABC, abstractmethod

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata


class SysadminPort(ABC):
    """Port for administrative operations on the EC Issuer."""

    @abstractmethod
    def update_credential_issuer_metadata(
        self, metadata: CredentialIssuerMetadata
    ) -> None:
        """Persist new credential issuer metadata.

        Args:
            metadata: The CredentialIssuerMetadata to store.
        """
        ...
