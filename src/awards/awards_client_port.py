"""Client port for awards operations."""

from abc import ABC, abstractmethod

from .models import OB3Award


class AwardNotFound(Exception):
    """Raised when the awards service returns 404."""


class AwardForbidden(Exception):
    """Raised when the awards service returns 403."""


class AwardsClientError(Exception):
    """Raised when awards service returns an unexpected error or invalid response."""


class AwardsClientPort(ABC):
    """Port: fetches awards from the external awards service.

    Returns OB3 AchievementCredential data — EDC issuance converts this via
    the credential converter, so there is no separate EDC fetch path.
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
