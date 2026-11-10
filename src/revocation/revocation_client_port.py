"""Client port for credential revocation operations."""

from abc import ABC, abstractmethod


class CredentialRevocationError(Exception):
    """Error raised when credential revocation fails."""


class RevocationClientPort(ABC):
    """Client port: Operations for credential revocation."""

    @abstractmethod
    def revoke(self, credential_id: str) -> None:
        """Revoke an issued credential by ID.

        Args:
            credential_id: The unique credential identifier to revoke.

        Raises:
            CredentialRevocationError: When revocation fails.
        """
        ...
