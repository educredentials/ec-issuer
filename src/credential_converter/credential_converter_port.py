"""Port for converting OB3 credentials to ELM/EDC format."""

from typing import Protocol


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


class CredentialConverterPort(Protocol):
    """Port: converts an OB3 credential to ELM/EDC format.

    Structural protocol — adapters and test stubs satisfy it by
    implementing ``convert`` without inheriting from this class.
    """

    def convert(self, credential: dict[str, object]) -> dict[str, object]:
        """Convert an OB3 credential to ELM/EDC format.

        Args:
            credential: The OB3 credential as a dict.

        Returns:
            The converted ELM/EDC credential as a dict.

        Raises:
            CredentialConverterClientError: On conversion failure.
        """
        ...