"""Domain model and port for the metadata repository."""

from abc import ABC, abstractmethod

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata


class MetadataNotFoundError(KeyError):
    """Exception raised when metadata is not found."""

    pass


class MetadataSerializationError(ValueError):
    """Exception raised when metadata serialization/deserialization fails."""

    pass


class MetadataRepositoryPort(ABC):
    """Port: repository interface for persisting and retrieving metadata."""

    @abstractmethod
    def store(self, metadata: CredentialIssuerMetadata) -> None:
        """Persist metadata.

        Args:
            metadata: The CredentialIssuerMetadata to store.
        """
        ...

    @abstractmethod
    def get(self) -> CredentialIssuerMetadata:
        """Retrieve the latest metadata entry.

        Returns:
            The CredentialIssuerMetadata.

        Raises:
            MetadataNotFoundError: When no metadata entry exists.
        """
        ...
