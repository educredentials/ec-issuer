"""Client port for awards operations."""

from abc import ABC, abstractmethod

from .models import Award


class AwardNotFound(Exception):
    """Raised when the awards service returns 404."""


class AwardForbidden(Exception):
    """Raised when the awards service returns 403."""


class AwardsClientError(Exception):
    """Raised when awards service returns an unexpected error or invalid response."""


class AwardsClientPort(ABC):
    """Port: fetches awards from the external awards service."""

    @abstractmethod
    def get(self, award_id: str) -> Award:
        """Fetch an award by its identifier.

        Args:
            award_id: The unique award identifier.

        Returns:
            The matching Award.

        Raises:
            AwardNotFound: When the award does not exist.
            AwardForbidden: When access to the award is denied.
            AwardsClientError: When the service returns an error or invalid response.
        """
        ...
