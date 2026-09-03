"""Domain models for awards (OB3 AchievementCredential)."""

from __future__ import annotations

from dataclasses import dataclass, field

import msgspec


class _BadgrIssuer(msgspec.Struct):
    """DTO for Badgr issuer within badgeclass."""

    name_dutch: str | None = None
    name_english: str | None = None
    faculty: object | None = None
    entity_id: str | None = None


class _BadgrBadgeclass(msgspec.Struct):
    """DTO for Badgr badgeclass."""

    id: int
    name: str
    entity_id: str | None = None
    description: str | None = None
    criteria_text: str | None = None
    issuer: _BadgrIssuer | None = None


class _BadgrAwardResponse(msgspec.Struct):
    """DTO for Badgr awards API response.

    Fields map to what the Badgr /earner/awards/{id} endpoint returns. Fields we do not
    need are intentionally omitted — msgspec ignores JSON keys with no matching Struct
    field, so new Badgr fields never break decoding.
    """

    id: int
    entity_id: str | None = None
    name: str | None = None
    issued_on: str | None = None
    badgeclass: _BadgrBadgeclass | None = None
    # Person/learner fields (populated when the awards service returns them).
    given_name: str | None = None
    family_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrAwardResponse:
        """Deserialize a dict to this DTO.

        Args:
            data: Raw dict from the Badgr API.

        Returns:
            A fully-typed _BadgrAwardResponse DTO.
        """
        return msgspec.convert(data, type=cls)


def _to_ob3_award(dto: _BadgrAwardResponse) -> OB3Award:
    """Convert a BadgrAwardResponse DTO to an OB3 Award domain model.

    Args:
        dto: The deserialized Badgr award response.

    Returns:
        A fully-structured OB3 Award.
    """
    entity_id = _resolve_entity_id(dto)
    badge_name = _resolve_badge_name(dto)
    issuer = _resolve_issuer(dto)
    valid_from = _resolve_valid_from(dto)
    achievement_data = _resolve_achievement_data(dto)

    return OB3Award(
        id=entity_id,
        type=["VerifiableCredential", "AchievementCredential"],
        name=badge_name,
        issuer=issuer,
        validFrom=valid_from,
        credentialSubject=AchievementSubject(
            id=entity_id,
            type=["AchievementSubject"],
            achievement=Achievement(
                id=entity_id,
                type=["Achievement"],
                criteria=Criteria(
                    narrative=achievement_data["criteria_text"],
                ),
                description=achievement_data["description"],
                name=badge_name,
            ),
        ),
    )


def _resolve_issuer(dto: _BadgrAwardResponse) -> Issuer:
    """Resolve the issuer from the DTO.

    Uses badgeclass.issuer.entity_id as the issuer id if available.
    Falls back to empty string.
    """
    badgeclass = dto.badgeclass
    if badgeclass is not None and badgeclass.issuer is not None:
        issuer_entity_id = badgeclass.issuer.entity_id or ""
    else:
        issuer_entity_id = ""
    return Issuer(
        id=issuer_entity_id,
        type=["Profile"],
        name=_resolve_badge_name(dto),
    )


def _resolve_achievement_data(dto: _BadgrAwardResponse) -> dict[str, str]:
    """Resolve achievement-level fields from the badgeclass.

    Returns criteria_text for the criteria.narrative and description for the
    achievement description.
    """
    badgeclass = dto.badgeclass
    criteria_text = ""
    description = ""
    if badgeclass is not None:
        if badgeclass.criteria_text:
            criteria_text = badgeclass.criteria_text
        if badgeclass.description:
            description = badgeclass.description
    return {"criteria_text": criteria_text, "description": description}


def _resolve_entity_id(dto: _BadgrAwardResponse) -> str:
    """Resolve the entity ID, falling back to str(id) if not set."""
    if dto.entity_id:
        return dto.entity_id
    return str(dto.id)


def _resolve_badge_name(dto: _BadgrAwardResponse) -> str:
    """Resolve the badge name, falling back to badgeclass.name if not set."""
    if dto.name:
        return dto.name
    if dto.badgeclass and dto.badgeclass.name:
        return dto.badgeclass.name
    return ""


def _resolve_valid_from(dto: _BadgrAwardResponse) -> str:
    """Resolve the validFrom date, falling back to empty string."""
    if dto.issued_on:
        return dto.issued_on
    return ""


def ob3_award_from_badgr_api_response(raw: dict[str, object]) -> OB3Award:
    """Convert a Badgr API response to an OB3 Award domain model.

    Args:
        raw: The parsed JSON response from the Badgr awards API.

    Returns:
        A fully-structured OB3 Award.
    """
    dto = _BadgrAwardResponse.from_dict(raw)
    return _to_ob3_award(dto)


@dataclass
class Criteria:
    """Criteria for earning an achievement."""

    narrative: str


@dataclass
class Achievement:
    """An achievement within an award."""

    id: str
    type: list[str]
    criteria: Criteria
    description: str
    name: str


@dataclass
class AchievementSubject:
    """The subject of an AchievementCredential."""

    id: str
    type: list[str]
    achievement: Achievement


@dataclass
class Issuer:
    """The issuer of an AchievementCredential."""

    id: str
    type: list[str]
    name: str


def _ob3_default_schema() -> list[dict[str, str]]:
    """Return the default OB3 credential schema."""
    return [
        {
            "id": "https://purl.imsglobal.org/spec/ob/v3p0/schema/json/ob_v3p0_achievementcredential_schema.json",
            "type": "1EdTechJsonSchemaValidator2019",
        }
    ]


@dataclass
class OB3Award:
    """Open Badges 3.0 AchievementCredential (unsigned)."""

    id: str
    type: list[str]
    name: str
    issuer: Issuer
    validFrom: str
    credentialSubject: AchievementSubject
    credentialSchema: list[dict[str, str]] = field(default_factory=_ob3_default_schema)


@dataclass
class EDCAward:
    """European Digital Credential claim set for SD-JWT VC.

    Flat structure — claims are selectively disclosable in SD-JWT format.

    VC envelope fields (issuer, issued, validUntil, @context, type, id) are
    handled by configuration and the SSI agent at issuance time, not by this
    dataclass.

    Args:
        given_name: Given name of the credential subject.
        family_name: Family name of the credential subject.
        valid_from: ISO 8601 datetime when the credential becomes valid.
            Determined by the awards service.
        learning_achievement: Learning achievement details.
            Expected keys: type, name, description.
        awarding_body: The body that awarded the credential.
            Expected keys: type, name, id.
        awarding_opportunity: The opportunity for which the credential was awarded.
            Expected keys: type, name.
        credential_schema: EU credential profile reference for VCDM v1.1.
            Maps to the VC credentialSchema property. Contains id (TSR reference)
            and type (schema validator type).
        subject_id: DID of the credential subject (learner).
            Comes from the award record.
    """

    given_name: str
    family_name: str
    valid_from: str
    learning_achievement: dict[str, object]
    awarding_body: dict[str, object]
    awarding_opportunity: dict[str, object]
    credential_schema: dict[str, str]
    subject_id: str


def _to_edc_award(dto: _BadgrAwardResponse) -> EDCAward:
    """Convert a BadgrAwardResponse DTO to an EDC Award domain model.

    Args:
        dto: The deserialized Badgr award response.

    Returns:
        A fully-structured EDC Award.
    """
    entity_id = _resolve_entity_id(dto)
    badge_name = _resolve_badge_name(dto)
    valid_from = _resolve_valid_from(dto)

    badgeclass = dto.badgeclass
    if badgeclass and badgeclass.issuer and badgeclass.issuer.name_english:
        issuer_name = badgeclass.issuer.name_english
    elif badgeclass and badgeclass.issuer and badgeclass.issuer.name_dutch:
        issuer_name = badgeclass.issuer.name_dutch
    else:
        issuer_name = ""
    issuer_id = badgeclass.issuer.entity_id if badgeclass and badgeclass.issuer else ""

    return EDCAward(
        given_name=dto.given_name or "",
        family_name=dto.family_name or "",
        valid_from=valid_from,
        learning_achievement={
            "name": badge_name,
            "description": badgeclass.description if badgeclass else "",
            "type": "achievement",
        },
        awarding_body={
            "name": issuer_name,
            "id": issuer_id,
            "type": "http://publications.europa.eu/ontology/authority#Authority",
        },
        awarding_opportunity={
            "name": badgeclass.name if badgeclass else "",
            "type": "http://data.europa.eu/snb/credential/25831c2",
        },
        credential_schema={
            "id": "http://data.europa.eu/snb/credential/25831c2",
            "type": "sd-jwt_vc+json",
        },
        subject_id=entity_id,
    )


def edc_award_from_badgr_api_response(raw: dict[str, object]) -> EDCAward:
    """Convert a Badgr API response to an EDC Award domain model.

    Args:
        raw: The parsed JSON response from the Badgr awards API.

    Returns:
        A fully-structured EDC Award.
    """
    dto = _BadgrAwardResponse.from_dict(raw)
    return _to_edc_award(dto)
