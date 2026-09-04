"""Port for the credential converter service.

The converter takes OB3 credentials and returns ELM/EDC JSON via an HTTP
endpoint that accepts base64-encoded payloads.
"""

from abc import ABC, abstractmethod


class CredentialConverterClientError(Exception):
    """Raised when the credential converter service returns an unexpected error."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialise the error.

        Args:
            message: Human-readable error description.
            cause: The original exception, if any.
        """
        super().__init__(message)
        self.cause: Exception | None = cause


class CredentialConverterPort(ABC):
    """Port: converts OB3 credentials to ELM/EDC JSON.

    Accepts a dict representing an OB3 credential and returns a dict
    representing the converted ELM/EDC credential (without ``@context``).

    Raises:
        CredentialConverterClientError: On any failure (network, conversion,
            or invalid response).
    """

    @abstractmethod
    def convert(self, credential: dict[str, object]) -> dict[str, object]:
        """Convert an OB3 credential to ELM/EDC format.

        Args:
            credential: The OB3 credential as a dict.

        Returns:
            The converted ELM/EDC credential as a dict.

        Raises:
            CredentialConverterClientError: On any failure.
        """
        ...