"""SSI-Agent Adapter for offer operations."""

from dataclasses import asdict, dataclass
from typing import override

import msgspec

from src.awards.models import Award
from src.lib.http_client import HttpClient, RequestsHttpClient

from .models import Offer
from .offers_client_port import (
    OfferNotFound,
    OffersClientError,
    OffersClientPort,
)


@dataclass
class _CredentialOffer:
    credential_issuer: str
    credential_configuration_ids: list[str]
    grants: dict[str, dict[str, str]]


@dataclass
class _SsiAgentOfferResponse:
    """SSI agent response on fetching a single offer from the admin api"""

    id: str
    grant_types: list[str]
    credential_offer_uri: dict[str, str]
    credential_offer: dict[str, _CredentialOffer]
    subject_id: str | None
    credential_ids: list[str]
    form_url_encoded_credential_offer: str
    pre_authorized_code: str
    credential_response: str | None
    status: str
    tx_code: str | None
    delivery_options: str | None


class SsiAgentOffersClientAdapter(OffersClientPort):
    """Adapter for SSI Agent offers API."""

    _ssi_agent_admin_base_url: str
    _http_client: HttpClient

    def __init__(
        self,
        ssi_agent_url: str,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            ssi_agent_url: The admin base URL of the SSI agent.
            http_client: The HTTP client to use for requests.
                Defaults to requests module.
        """
        self._ssi_agent_admin_base_url = ssi_agent_url.rstrip("/")
        if http_client is not None:
            self._http_client = http_client
        else:
            self._http_client = RequestsHttpClient()

    @override
    def create(self, offer_id: str, award: Award) -> str:
        """Create an offer in the SSI agent.

        Args:
            offer_id: The offer identifier to create.
            award: The award to issue as a credential.

        Returns:
            The credential offer URI.
        """
        self._create_credential_for_subject(offer_id, award)
        offer_uri = self._create_offer(offer_id)
        return offer_uri

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer from the SSI agent.

        Args:
            offer_id: The offer identifier to retrieve.

        Returns:
            The Offer object with the URI.

        Raises:
            OfferNotFound: When the offer is not found in the upstream service.
            OffersClientError: When upstream returns an error or invalid response.
        """
        response = self._http_client.get(
            f"{self._ssi_agent_admin_base_url}/v0/offers/{offer_id}",
        )

        if response.status_code == 404:
            raise OfferNotFound(f"Offer {offer_id} not found")

        if 400 <= response.status_code < 600:
            raise OffersClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        try:
            response_data: _SsiAgentOfferResponse = msgspec.json.decode(
                response.content, type=_SsiAgentOfferResponse
            )
        except msgspec.DecodeError as e:
            raise OffersClientError(f"Invalid response from upstream: {e}") from e

        uri: str = response_data.form_url_encoded_credential_offer

        return Offer(
            offer_id=offer_id,
            award_id="",
            uri=uri,
        )

    def _create_credential_for_subject(self, offer_id: str, award: Award) -> None:
        response = self._http_client.post(
            f"{self._ssi_agent_admin_base_url}/v0/credentials",
            json={
                "offerId": offer_id,
                "credential": asdict(award),
                "credentialConfigurationId": "openbadge_credential",
                "expiresAt": "3025-10-24 11:34:00Z",
            },
        )

        if 400 <= response.status_code < 600:
            raise OffersClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

    def _create_offer(self, offer_id: str) -> str:
        response = self._http_client.post(
            f"{self._ssi_agent_admin_base_url}/v0/offers",
            json={
                "offerId": offer_id,
                "credentialConfigurationIds": ["openbadge_credential"],
            },
        )

        if 400 <= response.status_code < 600:
            raise OffersClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        return response.text
