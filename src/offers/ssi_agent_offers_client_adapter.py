"""SSI-Agent Adapter for offer operations."""

from dataclasses import dataclass
from re import search as re_match
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
        credential["@context"] = self._assemble_context(award, "ob3", credential)
        _ = credential.pop("credential_context", None)
        _ = credential.pop("entity_id", None)
        self._attach_status_list(award.entity_id, credential)
        self._post_credential(
            offer_id,
            credential,
            self._credential_template_ids.get(CredentialType.OB3, ""),
        )
        offer_uri = self._post_offer(offer_id)
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
        credential["@context"] = self._assemble_context(None, "edc", credential)
        self._post_credential(
            offer_id,
            credential,
            self._credential_template_ids.get(CredentialType.EDC, ""),
        )
        offer_uri = self._post_offer(offer_id)
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

    def _assemble_context(
        self,
        award: OB3Award | None,
        credential_type: str,
        credential: dict[str, object],
    ) -> list[str | dict[str, str]]:
        """Build the @context list for OB3 or EDC credentials.

        Merges credential-specific extension contexts with hardcoded W3C
        and OpenBadges/EDC context URLs, providing a single shared method
        for both credential types.

        OB3: credential_context URLs are prepended, then hardcoded
        Open Badges / W3C contexts follow.

        EDC: hardcoded W3C contexts come first, then credential_context
        URLs (matching the legacy ``_edc_contexts`` behaviour).

        Args:
            award: The OB3 award for OB3 credentials, or ``None`` for EDC.
            credential_type: Either ``"ob3"`` or ``"edc"``.
            credential: The serialized credential dict (used for EDC
                extension contexts).

        Returns:
            The full @context array.
        """
        if credential_type == "ob3":
            assert award is not None, "award required for OB3 credentials"
            ctx = award.credential_context
        else:
            ctx = credential.get("credential_context") or []  # type: ignore[reportAssignmentType]

        if credential_type == "ob3":
            # OB3: extension contexts first, then hardcoded
            return list(chain(
                ctx or [],
                [
                    "https://www.w3.org/ns/credentials/v2",
                    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
                    "https://purl.imsglobal.org/spec/ob/v3p0/extensions.json",
                ],
            ))
        else:
            # EDC: hardcoded contexts first, then extension (legacy order)
            return list(chain(
                [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://www.w3.org/ns/credentials/v2",
                ],
                ctx or [],
            ))

    def _attach_status_list(
        self,
        entity_id: str | None,
        credential: dict[str, object],
    ) -> None:
        """Attach credentialStatus derived from the Badgr entity_id.

        Extracts the numeric idx from the entity_id URL (e.g.
        ``https://host/assertions/3527`` → idx 3527) and builds a
        ``credentialStatus`` dict matching the SSI-agent template.

        For non-numeric assertion IDs (e.g. UUIDs), derives a
        deterministic integer index using ``int.from_bytes``.

        If the entity_id is missing or the idx cannot be extracted,
        the credential is passed through unmodified.

        Args:
            entity_id: The entity_id from the award (may be None).
            credential: The credential dict to modify in place.
        """
        if not entity_id:
            return

        match = re_match(r"/assertions/([^/]+)$", entity_id)
        if not match:
            return

        captured = match.group(1)
        try:
            idx = int(captured)
        except ValueError:
            # Non-numeric assertion ID (e.g. UUID). Derive a
            # deterministic integer from the ID bytes.
            idx = int.from_bytes(captured.encode(), "big") % (2**31)

        status_base = self._ssi_agent_admin_base_url.rstrip("/")
        credential["credentialStatus"] = {
            "id": f"{entity_id}#{idx}",
            "type": "statuslist+jwt",
            "idx": idx,
            "uri": f"{status_base}/v0/status/{idx}",
        }

    def _post_credential(
        self,
        offer_id: str,
        credential: dict[str, object],
        template_id: str,
    ) -> None:
        """POST credential to SSI agent (/v0/credentials).

        Args:
            offer_id: The offer identifier.
            credential: The credential payload.
            template_id: The credential template ID.
        """
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

    def _post_offer(self, offer_id: str) -> str:
        """POST offer to SSI agent (/v0/offers).

        Args:
            offer_id: The offer identifier.

        Returns:
            The raw offer URI from the response body.
        """
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

    @override
    def rollback(self, offer_id: str) -> None:
        """Rollback a partially created offer.

        The SSI agent does not expose a delete endpoint for credentials or
        offers, so this is a no-op.  The repository store failure that
        triggers this path is expected to be transient (e.g. connection
        hiccup or unique constraint violation) and the partial credential
        and offer will be cleaned up by the SSI agent's garbage collection.

        Args:
            offer_id: The offer identifier to roll back.
        """
        ...
