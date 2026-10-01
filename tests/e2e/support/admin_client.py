"""Admin HTTP client for e2e tests."""

from dataclasses import dataclass

from msgspec import json as msgspec_json
from requests.models import Response

from .config import Config
from .http_client import HttpClient


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

    def create_offer(
        self,
        award_id: str,
        *,
        credential_type: str = "ob3",
    ) -> CreateOfferResponse:
        """Create a credential offer for an achievement.

        Args:
            award_id: The ID of the achievement to create an offer for.
            credential_type: The credential type — ``"ob3"`` (default) or ``"edc"``.

        Returns:
            CreateOfferResponse with offer_id and uri.
        """
        create_response: Response = self.post(
            "api/v1/offers",
            json={"award_id": award_id, "credential_type": credential_type},
        )
        assert create_response.status_code == 201, (
            f"Expected 201 Created, got {create_response.status_code}: "
            f"{create_response.text[:200]}"
        )

        return msgspec_json.decode(create_response.text, type=CreateOfferResponse)
