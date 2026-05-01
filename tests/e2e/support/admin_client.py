"""Admin HTTP client for e2e tests."""

from dataclasses import dataclass

from msgspec import json as msgspec_json
from requests.models import Response

from .http_client import HttpClient, Config


@dataclass
class CreateOfferResponse:
    """Response from creating a credential offer."""

    offer_id: str
    uri: str


class AdminHttpClient(HttpClient):
    """HTTP client for e2e tests that adds admin authentication headers."""

    def __init__(self, config: Config):
        """Initialise with service base URL from config and admin headers.

        Args:
            config: Test configuration.
        """
        super().__init__(config)
        self._default_headers: dict[str, str] = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }

    def create_offer(self, achievement_id: str) -> CreateOfferResponse:
        """Create a credential offer for an achievement.

        Args:
            achievement_id: The ID of the achievement to create an offer for.

        Returns:
            CreateOfferResponse with offer_id and uri.
        """
        create_response: Response = self.post(
            "api/v1/offers", json={"achievement_id": achievement_id}
        )
        assert create_response.status_code == 201, (
            f"Expected 201 Created, got {create_response.status_code}: "
            f"{create_response.text[:200]}"
        )

        return msgspec_json.decode(create_response.text, type=CreateOfferResponse)
