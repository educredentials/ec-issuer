from enum import Enum

from src.issuer_agent.issuer_agent_port import IssuerAgentPort
from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class MetadataService:
    issuer_agent: IssuerAgentPort
    public_url: str

    def __init__(self, issuer_agent: IssuerAgentPort, public_url: str) -> None:
        """Initialize the MetadataService.

        Args:
            issuer_agent: The issuer agent port.
            public_url: The publicly accessible base URL of this issuer service.
        """
        self.issuer_agent = issuer_agent
        self.public_url = public_url

    def get_health(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def get_credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Get credential issuer metadata with URLs replaced by our own.

        Returns:
            CredentialIssuerMetadata with credential_issuer and credential_endpoint
            replaced with our public_url.
        """
        metadata = self.issuer_agent.credential_issuer_metadata()
        return CredentialIssuerMetadata(
            credential_issuer=self.public_url,
            credential_endpoint=f"{self.public_url}/credential",
            credential_configurations_supported=metadata.credential_configurations_supported,
            authorization_servers=metadata.authorization_servers,
            nonce_endpoint=metadata.nonce_endpoint,
            deferred_credential_endpoint=metadata.deferred_credential_endpoint,
            notification_endpoint=metadata.notification_endpoint,
            credential_response_encryption=metadata.credential_response_encryption,
            batch_credential_issuance=metadata.batch_credential_issuance,
            display=metadata.display,
        )
