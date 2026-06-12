"""Service for award operations."""

from .awards_client_port import AwardsClientPort
from .models import Award


class AwardService:
    """Service that fetches awards from the awards client."""

    _client: AwardsClientPort

    def __init__(self, client: AwardsClientPort) -> None:
        """Initialize the service.

        Args:
            client: The port implementation for award operations.
        """
        self._client = client

    def get(self, award_id: str) -> Award:
        """Fetch an award by its identifier.

        Args:
            award_id: The unique award identifier.

        Returns:
            The matching Award.

        Raises:
            AwardNotFound: When the award does not exist.
            AwardForbidden: When access is denied.
            AwardsClientError: When the service errors.
        """
        return self._client.get(award_id)
