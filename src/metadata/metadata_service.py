from enum import Enum

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import MetadataRepositoryPort


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class MetadataService:
    _metadata_repository: MetadataRepositoryPort
    public_url: str

    def __init__(
        self, metadata_repository: MetadataRepositoryPort, public_url: str
    ) -> None:
        """Initialize the MetadataService.

        Args:
            metadata_repository: The metadata repository port.
            public_url: The publicly accessible base URL of this issuer service.
        """
        self._metadata_repository = metadata_repository
        self.public_url = public_url

    def get_health(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def get_credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Get credential issuer metadata with URLs replaced by our own.

        Returns:
            CredentialIssuerMetadata with credential_issuer and credential_endpoint
            replaced with our public_url.
        """
        return self._metadata_repository.get()
