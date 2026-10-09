"""Domain models for awards (OB3 AchievementCredential)."""

from __future__ import annotations

from dataclasses import dataclass, field

import msgspec


class AwardMappingError(Exception):
    """Raised when a Badgr award response cannot be mapped to an OB3 award."""


class _BadgrFaculty(msgspec.Struct):
    """DTO for faculty within issuer."""

    entity_id: str | None = msgspec.field(name="id", default=None)
    name_dutch: str | None = None
    name_english: str | None = None
    image_dutch: str | None = None
    image_english: str | None = None
    on_behalf_of: str | bool | None = None
    on_behalf_of_display_name: str | None = None
    on_behalf_of_url: str | None = None
    institution: _BadgrInstitution | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrFaculty:
        """Deserialize a dict to this DTO.

        Uses msgspec.field(name="id") so the JSON key ``id`` maps to the Python
        attribute ``entity_id`` without any pre-processing.
        """
        return msgspec.convert(data, type=cls)


class _BadgrInstitution(msgspec.Struct):
    """DTO for institution within faculty."""

    entity_id: str | None = msgspec.field(name="id", default=None)
    name_dutch: str | None = None
    name_english: str | None = None
    image_dutch: str | None = None
    image_english: str | None = None
    identifier: str | None = None
    alternative_identifier: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrInstitution:
        """Deserialize a dict to this DTO.

        Uses msgspec.field(name="id") so the JSON key ``id`` maps to the Python
        attribute ``entity_id`` without any pre-processing.
        """
        return msgspec.convert(data, type=cls)


class _BadgrIssuer(msgspec.Struct):
    """DTO for Badgr issuer within badgeclass."""

    entity_id: str | None = msgspec.field(name="id", default=None)
    name_dutch: str | None = None
    name_english: str | None = None
    faculty: _BadgrFaculty | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrIssuer:
        """Deserialize a dict to this DTO.

        Uses msgspec.field(name="id") so the JSON key ``id`` maps to the Python
        attribute ``entity_id`` without any pre-processing.  Nested dicts (e.g.
        ``faculty``) are converted automatically by msgspec.
        """
        return msgspec.convert(data, type=cls)


class _BadgrBadgeclass(msgspec.Struct):
    """DTO for Badgr badgeclass."""

    name: str
    entity_id: str | None = msgspec.field(name="id", default=None)
    description: str | None = None
    criteria_text: str | None = None
    image: str | None = msgspec.field(name="image", default=None)
    issuer: _BadgrIssuer | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrBadgeclass:
        """Deserialize a dict to this DTO.

        Uses msgspec.field(name="id") so the JSON key ``id`` maps to the Python
        attribute ``entity_id`` without any pre-processing.  Nested dicts (e.g.
        ``issuer``) are converted automatically by msgspec.
        """
        return msgspec.convert(data, type=cls)


class _BadgrAwardResponse(msgspec.Struct):
    """DTO for Badgr awards API response.

    Fields map to what the Badgr /earner/awards/{id} endpoint returns. Fields we do not
    need are intentionally omitted — msgspec ignores JSON keys with no matching Struct
    field, so new Badgr fields never break decoding.
    """

    entity_id: str | None = msgspec.field(name="id", default=None)
    name: str | None = None
    issued_on: str | None = None
    image: str | None = msgspec.field(name="image", default=None)
    badgeclass: _BadgrBadgeclass | None = None
    # Person/learner fields (populated when the awards service returns them).
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrAwardResponse:
        """Deserialize a dict to this DTO.

        Uses msgspec.field(name="id") so the JSON key ``id`` maps to the Python
        attribute ``entity_id`` without any pre-processing.  Nested dicts (e.g.
        ``badgeclass``, ``issuer``, ``faculty``) are converted automatically by
        msgspec.

        Args:
            data: Raw dict from the Badgr API.

        Returns:
            A fully-typed _BadgrAwardResponse DTO.
        """
        return msgspec.convert(data, type=cls)


def _to_ob3_award(
    dto: _BadgrAwardResponse,
    base_url: str | None = None,
) -> OB3Award:
    """Convert a BadgrAwardResponse DTO to an OB3 Award domain model.

    Args:
        dto: The deserialized Badgr award response.
        base_url: Optional base URL to resolve relative image paths to absolute
            URLs.

    Returns:
        A fully-structured OB3 Award.
    """
    credential_id = _resolve_credential_id(dto)
    badge_name = _resolve_badge_name(dto)
    issuer = _resolve_issuer(dto)
    valid_from = _resolve_valid_from(dto)
    achievement_data = _resolve_achievement_data(dto)
    identifiers = _resolve_identifiers(dto)
    image = _resolve_image(dto, base_url)

    return OB3Award(
        id=credential_id,
        type=["VerifiableCredential", "AchievementCredential"],
        name=badge_name,
        issuer=issuer,
        validFrom=valid_from,
        credentialSubject=AchievementSubject(
            id=credential_id,
            type=["AchievementSubject"],
            achievement=Achievement(
                id=credential_id,
                type=["Achievement"],
                criteria=Criteria(
                    narrative=achievement_data["criteria_text"],
                ),
                description=achievement_data["description"],
                name=badge_name,
                image=image,
            ),
            identifiers=identifiers,
        ),
    )


def _resolve_issuer(dto: _BadgrAwardResponse) -> Issuer:
    """Resolve the issuer from the DTO.

    Prefers badgeclass.issuer.entity_id (the id URI) and
    badgeclass.issuer.name_english (the issuer display name), falling back
    to badgeclass.name, then to empty string when absent.
    """
    badgeclass = dto.badgeclass
    issuer_name = ""
    if badgeclass is not None and badgeclass.issuer is not None:
        issuer_id = badgeclass.issuer.entity_id or ""
        issuer_name = badgeclass.issuer.name_english or ""
    else:
        issuer_id = ""
    if not issuer_name and badgeclass is not None:
        issuer_name = badgeclass.name or ""
    return Issuer(
        id=issuer_id,
        type=["Profile"],
        name=issuer_name,
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


def _resolve_credential_id(dto: _BadgrAwardResponse) -> str:
    """Resolve the credential ID from the ``id`` field.

    Returns:
        The URI from the source system.

    Raises:
        AwardMappingError: When the response has no ``id``.
    """
    if dto.entity_id:
        return dto.entity_id
    raise AwardMappingError("Badgr award response is missing 'id'")


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


def _resolve_image(
    dto: _BadgrAwardResponse,
    base_url: str | None = None,
) -> dict[str, str] | None:
    """Resolve the image from the badgeclass.

    When a ``base_url`` is provided and the image path is relative, it is
    resolved to an absolute URL.

    Args:
        dto: The deserialized Badgr award response.
        base_url: Optional base URL to resolve relative image paths.

    Returns:
        Image dict with ``id`` and ``type`` keys, or None.
    """
    raw_image = None
    if dto.badgeclass is not None and dto.badgeclass.image:
        raw_image = dto.badgeclass.image

    if raw_image is None:
        return None

    image_id = raw_image
    # Resolve relative paths to absolute URLs using the base URL.
    if base_url is not None and not raw_image.startswith(("http://", "https://")):
        image_id = f"{base_url.rstrip('/')}{raw_image}"

    return {"id": image_id, "type": "Image"}


def _resolve_identifiers(dto: _BadgrAwardResponse) -> list[IdentityObject]:
    """Build an identifier list from recipient data in the DTO.

    Collects plain-text identifiers for email and name when present.
    """
    identifiers: list[IdentityObject] = []
    if dto.email:
        identifiers.append(
            IdentityObject(
                type=["IdentityObject"],
                identityHash=dto.email,
                identityType="emailAddress",
                hashed=False
            )
        )
    name = _resolve_name(dto)
    if name:
        identifiers.append(
            IdentityObject(
                type=["IdentityObject"],
                identityHash=name,
                identityType="name",
                hashed=False,
            )
        )
    return identifiers


def _resolve_name(dto: _BadgrAwardResponse) -> str:
    """Resolve the recipient full name from given_name + family_name."""
    parts = [p for p in (dto.given_name, dto.family_name) if p]
    return " ".join(parts)


def ob3_award_from_badgr_api_response(
    raw: dict[str, object],
    base_url: str | None = None,
) -> OB3Award:
    """Convert a Badgr API response to an OB3 Award domain model.

    Args:
        raw: The parsed JSON response from the Badgr awards API.
        base_url: Optional base URL to resolve relative image paths to absolute
            URLs. Required when the image field contains a relative path.

    Returns:
        A fully-structured OB3 Award.
    """
    dto = _BadgrAwardResponse.from_dict(raw)
    return _to_ob3_award(dto, base_url)


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
    image: dict[str, str] | None = None


@dataclass
class AchievementSubject:
    """The subject of an AchievementCredential."""

    id: str
    type: list[str]
    achievement: Achievement
    identifiers: list[IdentityObject] = field(default_factory=list)


@dataclass
class Issuer:
    """The issuer of an AchievementCredential."""

    id: str
    type: list[str]
    name: str


@dataclass
class IdentityObject:
    """An identifier for the recipient of an achievement (OB3 spec)."""

    type: list[str]
    identityHash: str
    identityType: str
    hashed: bool


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
