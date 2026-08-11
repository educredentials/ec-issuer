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

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "_BadgrAwardResponse":
        """Deserialize a dict to this DTO.

        Args:
            data: Raw dict from the Badgr API.

        Returns:
            A fully-typed _BadgrAwardResponse DTO.
        """
        return msgspec.convert(data, type=cls)


def _to_ob3_award(dto: "_BadgrAwardResponse") -> Award:
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

    return Award(
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


def award_from_badgr_api_response(raw: dict[str, object]) -> Award:
    """Convert a Badgr API response to an OB3 Award domain model.

    Args:
        raw: The parsed JSON response from the Badgr awards API.

    Returns:
        A fully-structured Award.
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
class Award:
    """Minimal OB3 AchievementCredential (unsigned)."""

    id: str
    type: list[str]
    name: str
    issuer: Issuer
    validFrom: str
    credentialSubject: AchievementSubject
    credentialSchema: list[dict[str, str]] = field(default_factory=_ob3_default_schema)
