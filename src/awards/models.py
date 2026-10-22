"""Domain models for awards (OB3 AchievementCredential)."""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import cast

import msgspec

log = logging.getLogger(__name__)


class AwardMappingError(Exception):
    """Raised when a Badgr award response cannot be mapped to an OB3 award."""


class AssessmentType(StrEnum):
    """Assessment type per Open Badges AssessmentTypeExtension."""

    TESTING = "testing"
    APPLICATION_OF_SKILL = "applicationOfSkill"
    PORTFOLIO = "portfolio"
    RECOGNITION_OF_PRIOR_LEARNING = "recognitionOfPriorLearning"
    PERSONALIZED_ASSESSMENT = "personalizedAssessment"
    BY_CHOICE_OF_PARTICIPANT = "byChoiceOfParticipant"

    # Allow arbitrary values from the awards service.
    @classmethod
    def _missing_(cls, value: object) -> "AssessmentType | None":  # pyright: ignore[reportImplicitOverride]
        if isinstance(value, str):
            return cls(value)
        return None


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


class _BadgrCriteria(msgspec.Struct):
    """DTO for the ``criteria`` object inside ``badgeclass``."""

    narrative: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrCriteria:
        """Deserialize a dict to this DTO."""
        return msgspec.convert(data, type=cls)


class _BadgrBadgeclass(msgspec.Struct):
    """DTO for Badgr badgeclass."""

    name: str
    entity_id: str | None = msgspec.field(name="id", default=None)
    description: str | None = None
    criteria_text: str | None = None
    image: str | None = msgspec.field(name="image", default=None)
    criteria: _BadgrCriteria | None = None
    issuer: _BadgrIssuer | None = None
    # Flat extension fields (top-level on badgeclass).
    participation: str | None = None
    assessment_type: str | None = None
    assessment_id_verified: bool | None = None
    assessment_supervised: bool | None = None
    # Array of extension objects from the awards service.
    extensions: list[dict[str, object]] | None = None

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
    # Extended fields from the awards service.
    expires_at: str | None = msgspec.field(name="expires_at", default=None)
    language: str | None = msgspec.field(name="language", default=None)
    ects: float | None = msgspec.field(name="ects", default=None)
    eqf: int | None = msgspec.field(name="eqf", default=None)
    participation: str | None = msgspec.field(name="participation", default=None)
    assessment_type: str | None = msgspec.field(
        name="assessment_type", default=None
    )
    assessment_id_verified: bool | None = msgspec.field(
        name="assessment_id_verified", default=None
    )
    assessment_supervised: bool | None = msgspec.field(
        name="assessment_supervised", default=None
    )
    learning_outcome: list[dict[str, str]] | None = msgspec.field(
        name="learning_outcome", default=None
    )
    education_program_identifier: list[str] | None = msgspec.field(
        name="education_program_identifier", default=None
    )

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


class _BadgeclassExtensions(msgspec.Struct):
    """Typed extension values extracted from ``badgeclass.extensions``."""

    language: str | None = None
    ects: float | None = None
    eqf: int | None = None
    learning_outcome: list[dict[str, str]] | None = None
    education_program_identifier: list[str] | None = None


_EXT_MAP: dict[str, str] = {
    "extensions:LanguageExtension": "language",
    "extensions:ECTSExtension": "ects",
    "extensions:EQFExtension": "eqf",
    "extensions:LearningOutcomeExtension": "learning_outcome",
    "extensions:EducationProgramIdentifierExtension": "education_program_identifier",
}

# Maps snake_case field names to the actual keys in originalJson (camelCase).
_ORIGINAL_JSON_KEY_MAP: dict[str, str] = {
    "language": "Language",
    "ects": "ECTS",
    "eqf": "EQF",
    "learning_outcome": "learningOutcomes",
    "education_program_identifier": "EducationProgramIdentifier",
}


def _extract_extension_values(
    badgeclass: _BadgrBadgeclass | None,
) -> _BadgeclassExtensions:
    """Extract extension values from ``badgeclass.extensions``.

    The awards service embeds extension data inside ``extensions`` entries
    whose ``originalJson`` contains keys like ``Language``, ``ECTS``, ``EQF``,
    ``learningOutcomes`` and ``EducationProgramIdentifier``.
    """
    if badgeclass is None or badgeclass.extensions is None:
        log.debug("_extract_extension_values: badgeclass is None or has no extensions")
        return _BadgeclassExtensions()

    vals: dict[str, object] = {}
    for ext in badgeclass.extensions:
        ext_name = str(ext.get("name", ""))
        original = ext.get("originalJson", {})
        log.debug(
            "_extract_extension_values: ext_name=%s, original=%s",
            ext_name,
            original,
        )
        if not isinstance(original, dict):
            continue
        if ext_name not in _EXT_MAP:
            continue
        field_name = _EXT_MAP[ext_name]
        json_key = _ORIGINAL_JSON_KEY_MAP.get(field_name, field_name)
        vals[field_name] = original.get(json_key)

    _lang = vals.get("language")
    _ects = vals.get("ects")
    _eqf = vals.get("eqf")
    _lo = vals.get("learning_outcome")
    _epi = vals.get("education_program_identifier")
    log.debug(
        "_extract_extension_values: extracted vals=%s",
        vals,
    )

    return _BadgeclassExtensions(
        language=str(_lang) if _lang is not None else None,
        ects=float(_ects) if isinstance(_ects, (int, float)) else None,
        eqf=int(_eqf) if isinstance(_eqf, int) else None,
        learning_outcome=_lo if isinstance(_lo, list) else None,
        education_program_identifier=(
            [str(v) for v in _epi] if isinstance(_epi, list) else None
        ),
    )


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

    valid_to = dto.expires_at
    badgeclass = dto.badgeclass
    ext_vals = _extract_extension_values(badgeclass)
    credential_context = _credential_context_urls(
        badgeclass=badgeclass, ext_vals=ext_vals
    )

    # Extension fields from badgeclass.extensions.originalJson take priority.
    language = ext_vals.language or dto.language
    ects = ext_vals.ects or dto.ects
    eqf = ext_vals.eqf or dto.eqf
    learning_outcome = ext_vals.learning_outcome or dto.learning_outcome
    education_program_identifier = (
        ext_vals.education_program_identifier
        or dto.education_program_identifier
    )

    # Flat extension fields from badgeclass level.
    participation = (
        (badgeclass.participation if badgeclass else None)
        or dto.participation
    )
    assessment_type = (
        (badgeclass.assessment_type if badgeclass else None)
        or dto.assessment_type
    )
    assessment_id_verified = (
        badgeclass.assessment_id_verified
        if badgeclass and badgeclass.assessment_id_verified is not None
        else dto.assessment_id_verified
    )
    assessment_supervised = (
        badgeclass.assessment_supervised
        if badgeclass and badgeclass.assessment_supervised is not None
        else dto.assessment_supervised
    )

    return OB3Award(
        id=credential_id,
        type=["VerifiableCredential", "AchievementCredential"],
        name=badge_name,
        issuer=issuer,
        validFrom=valid_from,
        validUntil=valid_to,
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
                language=language,
                ects=ects,
                eqf=eqf,
                learning_outcome=learning_outcome,
                education_program_identifier=education_program_identifier,
                participation=participation,
                assessment_type=assessment_type,
                assessment_id_verified=assessment_id_verified,
                assessment_supervised=assessment_supervised,
            ),
            identifiers=identifiers,
        ),
        credential_context=credential_context,
    )


def _credential_context_urls(
    *,
    badgeclass: _BadgrBadgeclass | None,
    ext_vals: _BadgeclassExtensions,
) -> list[str]:
    """Return the list of credential context URLs for non-None flat fields.

    The URLs are built from ``EC_ISSUER_URL`` when set, otherwise
    ``http://localhost:8000``.  Only non-None flat fields contribute a
    context URL.
    """
    base = (
        os.environ.get("EC_ISSUER_URL")
        or "http://localhost:8000"
    ).rstrip("/")

    ext_dir = "/static/extensions"
    bc = badgeclass if badgeclass else _BadgrBadgeclass(
        name="", entity_id=None
    )
    ext_map: list[tuple[str, object]] = [
        ("ParticipationFormExtension/context.json", bc.participation),
        ("AssessmentTypeExtension/context.json", bc.assessment_type),
        ("LanguageExtension/context.json", ext_vals.language),
        ("ECTSExtension/context.json", ext_vals.ects),
        ("EQFExtension/context.json", ext_vals.eqf),
        ("LearningOutcomeExtension/context.json", ext_vals.learning_outcome),
        (
            "EducationProgramIdentifierExtension/context.json",
            ext_vals.education_program_identifier,
        ),
    ]

    return [
        f"{base}{ext_dir}/{filename}"
        for filename, field_value in ext_map
        if field_value is not None
    ]


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
        # The awards service embeds criteria under badgeclass.criteria.narrative.
        if (
            badgeclass.criteria is not None
            and badgeclass.criteria.narrative
        ):
            criteria_text = badgeclass.criteria.narrative
        elif badgeclass.criteria_text:
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


def ob3_award_to_json_dict(award: OB3Award) -> dict[str, object]:
    """Serialize an OB3Award to a dict, omitting None values.

    This is the counterpart to ``asdict`` that excludes fields with None values
    so they do not appear as null in the JSON output.
    """
    return cast(dict[str, object], _remove_none(asdict(award)))


def _remove_none(obj: object) -> object:
    """Recursively remove None values from dicts and lists."""
    if isinstance(obj, dict):
        return {k: _remove_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_remove_none(item) for item in obj if item is not None]
    return obj


@dataclass
class Criteria:
    """Criteria for earning an achievement."""

    narrative: str = ""


@dataclass
class Achievement:
    """An achievement within an award."""

    id: str
    type: list[str]
    criteria: Criteria
    description: str
    name: str
    image: dict[str, str] | None = None
    language: str | None = None
    ects: float | None = None
    eqf: int | None = None
    learning_outcome: list[dict[str, str]] | None = None
    education_program_identifier: list[str] | None = None
    participation: str | None = None
    assessment_type: str | None = None
    assessment_id_verified: bool | None = None
    assessment_supervised: bool | None = None


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
    """Open Badges 3.0 AchievementCredential (unsigned).

    Fields beyond the OB3 core spec represent VCDM 2.0 extension properties.
    They are serialized to JSON as top-level credential keys, not wrapped
    in an ``extensions`` array, and are validated against the SSI-agent
    template schema.  ``credential_context`` carries the ``@context`` URLs
    needed by the SSI agent for signing.
    """

    id: str
    type: list[str]
    name: str
    issuer: Issuer
    validFrom: str
    credentialSubject: AchievementSubject
    credentialSchema: list[dict[str, str]] = field(default_factory=_ob3_default_schema)
    # --- OB3 / VCDM 2.0 extension properties ---
    validUntil: str | None = None
    # Context for SSI-agent signing.
    credential_context: list[str] | None = None
