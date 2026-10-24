"""SSI-Agent Adapter for offer operations."""

from dataclasses import dataclass
from typing import override
from itertools import chain

import msgspec

from src.awards.models import OB3Award, ob3_award_to_json_dict
from src.lib.http_client import HttpClient, RequestsHttpClient

from .models import CredentialType, Offer
from .offers_client_port import (
    OfferNotFound,
    OffersClientError,
    OffersClientPort,
)


@dataclass
class _CredentialOffer:
    credential_issuer: str
    credential_template_id: str
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
    _credential_template_ids: dict[CredentialType, str]

    def __init__(
        self,
        ssi_agent_url: str,
        credential_template_ids: dict[CredentialType, str] | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            ssi_agent_url: The admin base URL of the SSI agent.
            credential_template_ids: The credential template IDs to use
                for offers, keyed by ``CredentialType``.
            http_client: The HTTP client to use for requests.
                Defaults to requests module.
        """
        self._ssi_agent_admin_base_url = ssi_agent_url.rstrip("/")
        self._credential_template_ids = credential_template_ids or {}
        if http_client is not None:
            self._http_client = http_client
        else:
            self._http_client = RequestsHttpClient()

    @override
    def create_ob3(self, offer_id: str, award: OB3Award) -> str:
        """Create an OB3 credential offer in the SSI agent.

        Args:
            offer_id: The offer identifier to create.
            award: The OB3 AchievementCredential to issue.

        Returns:
            The credential offer URI.
        """
        credential = ob3_award_to_json_dict(award)
        credential["@context"] = self._ob3_contexts(award)
        _ = credential.pop("credential_context", None)
        self._create_credential_for_subject(
            offer_id,
            credential,
            self._credential_template_ids.get(CredentialType.OB3, ""),
        )
        offer_uri = self._create_offer(offer_id)
        return offer_uri

    @override
    def create_edc(
        self, offer_id: str, credential: dict[str, object]
    ) -> str:
        """Create an EDC credential offer in the SSI agent.

        Args:
            offer_id: The offer identifier to create.
            credential: The ELM/EDC credential as a dict.

        Returns:
            The credential offer URI.
        """
        credential["@context"] = self._edc_contexts(credential)
        self._create_credential_for_subject(
            offer_id,
            credential,
            self._credential_template_ids.get(CredentialType.EDC, ""),
        )
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

    def _ob3_contexts(self, award: OB3Award) -> list[str]:
        """Return the hardcoded @context list for an OpenBadgeCredential.

        Args:
            credential: The serialized OB3 credential

        Returns:
            The Open Badges 3.0 context array with
            ``${SSI_AGENT_URL}`` substituted from the SSI agent base URL.
        """
        return list(chain([
            "https://www.w3.org/ns/credentials/v2",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
            "https://purl.imsglobal.org/spec/ob/v3p0/extensions.json",
        ], award.credential_context or []))

    def _edc_contexts(self, credential: dict[str, object]) -> list[str]:
        """Return the hardcoded @context list for a EuropeanDigitalCredential.

        Args:
            credential: The serialized EDC credential

        Returns:
            The EDC/W3C 2.0 context array.
        """
        credential_context: list[str] = credential["credential_context"]  # pyright: ignore[reportAssignmentType]
        return list(chain([
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/ns/credentials/v2",
        ], credential_context))

    def _create_credential_for_subject(
        self,
        offer_id: str,
        credential: dict[str, object],
        template_id: str,
    ) -> None:
        response = self._http_client.post(
            f"{self._ssi_agent_admin_base_url}/v0/credentials",
            json={
                "offerId": offer_id,
                "credential": credential,
                "templateId": template_id,
                "expiresAt": "never",
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
                "templateIds": list(self._credential_template_ids.values()),
            },
        )

        if 400 <= response.status_code < 600:
            raise OffersClientError(
                f"Upstream error: {response.status_code} - {response.content.decode()}"
            )

        return response.text
