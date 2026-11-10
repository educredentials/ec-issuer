"""SSI-Agent Adapter for offer operations."""

import json
import logging
from dataclasses import dataclass
from re import search as re_match
from typing import cast, override
from itertools import chain

import msgspec

from src.awards.models import OB3Award, ob3_award_to_json_dict
from src.lib.http_client import HttpClient, RequestsHttpClient

from .models import CredentialType, Offer
from .offers_client_port import (
    OfferCreated,
    OfferNotFound,
    OffersClientError,
    OffersClientPort,
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
if not log.handlers:
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.DEBUG)
    _fmt = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    _handler.setFormatter(logging.Formatter(_fmt))
    log.addHandler(_handler)

# The SSI agent requires these 3 base OB3 contexts to appear first
# in the @context array.
_OB3_BASE_CONTEXTS: list[str] = [
    "https://www.w3.org/ns/credentials/v2",
    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
    "https://purl.imsglobal.org/spec/ob/v3p0/extensions.json",
]


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
    def create_ob3(self, offer_id: str, award: OB3Award) -> OfferCreated:
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
        log.info(
            "Assembled OB3 credential:\n%s",
            json.dumps(credential, indent=2),
        )
        self._post_credential(
            offer_id,
            credential,
            self._credential_template_ids.get(CredentialType.OB3, ""),
        )
        offer_created = self._post_offer(offer_id)
        return offer_created

    @override
    def create_edc(
        self, offer_id: str, credential: dict[str, object]
    ) -> OfferCreated:
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
        offer_created = self._post_offer(offer_id)
        return offer_created

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
            credential_ids=response_data.credential_ids,
        )

    def _assemble_context(
        self,
        award: OB3Award | None,
        credential_type: str,
        credential: dict[str, object],
    ) -> list[str | dict[str, str]]:
        """Build the @context for OB3 or EDC credentials.

        The SSI agent requires ``@context`` to be an array with the 3
        base OB3 contexts first, then any extension URLs and inline
        JSON-LD term definitions.

        EDC keeps the legacy behaviour: hardcoded W3C contexts first,
        then credential_context URLs.

        Args:
            award: The OB3 award for OB3 credentials, or ``None`` for EDC.
            credential_type: Either ``"ob3"`` or ``"edc"``.
            credential: The serialized credential dict (used for EDC
                extension contexts).

        Returns:
            The @context array: base OB3 contexts first, then URLs and
            inline term definitions for OB3; a multi-element list for EDC.
        """
        if credential_type == "ob3":
            assert award is not None, "award required for OB3 credentials"
            # The SSI agent requires the 3 base OB3 contexts first.
            # The award.credential_context contains [inline_ctx, *urls, *base_ctxs]
            # so we extract the non-base elements and reorder.
            ctx_elements = award.credential_context or []
            inline_ctx: dict[str, str] | None = None
            extension_urls: list[str] = []
            for elem in ctx_elements:
                if isinstance(elem, dict):
                    inline_ctx = elem  # type: ignore[assignment]
                elif elem in _OB3_BASE_CONTEXTS:
                    continue  # skip — we add base contexts first below
                else:
                    extension_urls.append(elem)
            # base contexts → extension URLs → inline term definitions
            return [* _OB3_BASE_CONTEXTS, *extension_urls, * (
                [inline_ctx] if inline_ctx is not None else []
            )]
        else:
            # EDC: hardcoded contexts first, then extension (legacy order)
            return list(chain(
                [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://www.w3.org/ns/credentials/v2",
                ],
                cast(
                    list[str | dict[str, str]],
                    credential.get("credential_context"),
                ) or [],
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

    def _post_offer(self, offer_id: str) -> OfferCreated:
        """POST offer to SSI agent (/v0/offers).

        Args:
            offer_id: The offer identifier.

        Returns:
            The offer URI and credential IDs.
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

        uri: str = response.text
        # Fetch credential_ids from the offer response
        credential_ids: list[str] | None = None
        try:
            offer_response = self._http_client.get(
                f"{self._ssi_agent_admin_base_url}/v0/offers/{offer_id}"
            )
            if offer_response.status_code == 200:
                offer_data: _SsiAgentOfferResponse = msgspec.json.decode(
                    offer_response.content, type=_SsiAgentOfferResponse
                )
                credential_ids = offer_data.credential_ids
        except Exception:
            # If we can't fetch credential_ids, continue without them
            # They can be fetched later via get()
            pass

        return OfferCreated(
            uri=uri,
            credential_ids=credential_ids,
        )

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
