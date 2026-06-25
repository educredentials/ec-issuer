"""HTTP adapter for the awards service."""

from typing import override

import msgspec

from src.lib.http_client import HttpClient, RequestsHttpClient

from .awards_client_port import (
    AwardForbidden,
    AwardNotFound,
    AwardsClientError,
    AwardsClientPort,
)
from .models import Award


class HttpAwardsClientAdapter(AwardsClientPort):
    """
    Adapter for the awards HTTP service. This maps to the stoplight mock. Not
    yet to the STRAPI API!, that would make this a "StrapiAwardsClientAdapter".
    """

    _awards_service_base_url: str
    _http_client: HttpClient

    def __init__(
        self,
        awards_service_url: str,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            awards_service_url: The base URL of the awards service.
            http_client: The HTTP client to use. Defaults to requests.
        """
        self._awards_service_base_url = awards_service_url.rstrip("/")
        if http_client is not None:
            self._http_client = http_client
        else:
            self._http_client = RequestsHttpClient()

    @override
    def get(self, award_id: str) -> Award:
        """Fetch an award by ID from the awards HTTP service.

        Args:
            award_id: The unique award identifier.

        Returns:
            The matching Award.

        Raises:
            AwardNotFound: On 404.
            AwardForbidden: On 403.
            AwardsClientError: On other errors or invalid response.
        """
        response = self._http_client.get(
            f"{self._awards_service_base_url}/awards/{award_id}"
        )

        if response.status_code == 404:
            raise AwardNotFound(f"Award {award_id} not found")

        if response.status_code == 403:
            raise AwardForbidden(f"Access to award {award_id} denied")

        if 400 <= response.status_code < 600:
            raise AwardsClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        try:
            return msgspec.json.decode(response.content, type=Award)
        except msgspec.DecodeError as e:
            raise AwardsClientError(f"Invalid response from awards service: {e}") from e
