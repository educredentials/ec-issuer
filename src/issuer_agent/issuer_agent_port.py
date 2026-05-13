"""Issuer Agent Port module."""

from abc import ABC, abstractmethod

from src.credentials.credential import CredentialResponse
from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata


class MetadataError(Exception):
    """Exception raised when there is an error in the metadata."""

    pass


class IssuerAgentError(Exception):
    """Exception raised when there is an error in the issuer agent."""

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
    def credential_request(
        self,
        format: str,
        credential_configuration_id: str,
        proof: dict[str, object],
        issuer_state: str,
        access_token: str,
    ) -> CredentialResponse:
        """Request a credential from the issuer agent.

        Args:
            format: The credential format.
            credential_configuration_id: The credential configuration identifier.
            proof: The proof object containing proof_type and jwt.
            issuer_state: The issuer state from the offer.
            access_token: The access token for authorization.

        Returns:
            CredentialResponse containing the issued credential(s).
        """
        ...

    @abstractmethod
    def request_nonce(self) -> dict[str, str]:
        """Request a nonce from the issuer agent.

        Returns:
            A dictionary containing the c_nonce.
        """
        ...
