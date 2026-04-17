from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


@dataclass
class Image:
    uri: str
    alt_text: str | None = None


@dataclass
class Display:
    name: str
    locale: str | None = None
    logo: Image | None = None
    description: str | None = None
    background_color: str | None = None
    background_image: Image | None = None
    text_color: str | None = None


@dataclass
class KeyAttestation:
    key_storage: list[str] | None = None
    user_authentication: list[str] | None = None


@dataclass
class ProofType:
    proof_signing_alg_values_supported: list[str]
    key_attestations_required: dict[str, KeyAttestation] | None = None


@dataclass
class CredentialConfiguration:
    format: str
    scope: str | None = None
    cryptographic_binding_methods_supported: list[str] | None = None
    credential_signing_alg_values_supported: list[str] | None = None
    proof_types_supported: dict[str, ProofType] | None = None
    display: list[Display] | None = None


@dataclass
class CredentialResponseEncryption:
    alg_values_supported: list[str]
    enc_values_supported: list[str]
    encryption_required: bool


@dataclass
class BatchCredentialIssuance:
    batch_size: int


@dataclass
class CredentialIssuerMetadata:
    credential_issuer: str
    credential_endpoint: str
    credential_configurations_supported: dict[str, CredentialConfiguration]
    authorization_servers: list[str] | None = None
    nonce_endpoint: str | None = None
    deferred_credential_endpoint: str | None = None
    notification_endpoint: str | None = None
    credential_response_encryption: dict[str, CredentialResponseEncryption] | None = (
        None
    )
    batch_credential_issuance: dict[str, BatchCredentialIssuance] | None = None
    display: list[Display] | None = None


class IssuerAgentPort(ABC):
    """Port for Issuer Agent Adapters."""

    @abstractmethod
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Return Credential Issuer Metadata.

        Args:
            request: The Flask request object.

        Returns:
            A ResponseProtocol object containing the response.
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
