"""Sysadmin service implementing administrative operations."""

from typing import override

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import MetadataRepositoryPort

from .sysadmin_port import SysadminPort


class SysadminService(SysadminPort):
    """Service that executes sysadmin operations against the metadata repository."""

    _metadata_repository: MetadataRepositoryPort

    def __init__(self, metadata_repository: MetadataRepositoryPort) -> None:
        """Initialise with the metadata repository.

        Args:
            metadata_repository: The repository to persist metadata to.
        """
        self._metadata_repository = metadata_repository

    @override
    def update_credential_issuer_metadata(
        self, metadata: CredentialIssuerMetadata
    ) -> None:
        """Persist new credential issuer metadata.

        Args:
            metadata: The CredentialIssuerMetadata to store.
        """
        self._metadata_repository.store(metadata)
