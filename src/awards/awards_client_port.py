"""Client port for awards operations."""

from abc import ABC, abstractmethod

from .models import EDCAward, OB3Award


class AwardNotFound(Exception):
    """Raised when the awards service returns 404."""


class AwardForbidden(Exception):
    """Raised when the awards service returns 403."""


class AwardsClientError(Exception):
    """Raised when awards service returns an unexpected error or invalid response."""


class AwardsClientPort(ABC):
    """Port: fetches awards from the external awards service.

    Split into credential-type-specific methods so that each path has its own
    conversion from the raw Badgr response — EDCAward never depends on OB3Award.
    """

    @abstractmethod
    def get_ob3(self, award_id: str, bearer_token: str) -> OB3Award:
        """Fetch and convert an award to an OB3 AchievementCredential.

        Args:
            award_id: The unique award identifier.
            bearer_token: The caller's bearer token for authentication.

        Returns:
            The matching OB3 Award.

        Raises:
            AwardNotFound: When the award does not exist.
            AwardForbidden: When access to the award is denied.
            AwardsClientError: When the service returns an error or invalid response.
        """
        ...

    @abstractmethod
    def get_edc(self, award_id: str, bearer_token: str) -> EDCAward:
        """Fetch and convert an award to an EDC claim set.

        Args:
            award_id: The unique award identifier.
            bearer_token: The caller's bearer token for authentication.

        Returns:
            The matching EDC Award.

        Raises:
            AwardNotFound: When the award does not exist.
            AwardForbidden: When access to the award is denied.
            AwardsClientError: When the service returns an error or invalid response.
        """
        ...
