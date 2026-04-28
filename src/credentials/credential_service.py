"""Credential service for requesting credentials."""

from src.credentials.credential import CredentialResponse
from src.issuer_agent.issuer_agent_port import IssuerAgentPort


class CredentialService:
    """Service that orchestrates credential requests."""

    _issuer_agent: IssuerAgentPort

    def __init__(self, issuer_agent: IssuerAgentPort) -> None:
        """Initialise the service with its dependencies.

        Args:
            issuer_agent: Adapter for the SSI agent that handles credential requests.
        """
        self._issuer_agent = issuer_agent

    def request_credential(
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
        return self._issuer_agent.credential_request(
            format=format,
            credential_configuration_id=credential_configuration_id,
            proof=proof,
            issuer_state=issuer_state,
            access_token=access_token,
        )

    def request_nonce(self) -> dict[str, str]:
        """Request a nonce from the issuer agent.

        Returns:
            A dictionary containing the c_nonce.
        """
        return self._issuer_agent.request_nonce()
