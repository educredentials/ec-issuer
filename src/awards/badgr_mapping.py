"""Badgr DTOs and mapping to OB3 award domain model.

This module lives at the adapter boundary. It contains:

* Badgr-specific DTOs (_Badgr*) — not part of the domain model
* Mapping logic from Badgr API responses to ``OB3Award``
* Pure function ``_credential_context_urls`` — builds credential context URLs
  from injected base URLs (no environment reads).
"""

from __future__ import annotations

import logging

import msgspec

from src.awards.models import (
    Achievement,
    AchievementSubject,
    Criteria,
    IdentityObject,
    Issuer,
    OB3Award,
)

log = logging.getLogger(__name__)


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
        """Deserialize a dict to this DTO."""
        return msgspec.convert(data, type=cls)


class _BadgrIssuer(msgspec.Struct):
    """DTO for Badgr issuer within badgeclass."""

    entity_id: str | None = msgspec.field(name="id", default=None)
    name_dutch: str | None = None
    name_english: str | None = None
    faculty: _BadgrFaculty | None = None
    # Flat extension field from the issuer.
    type: str | None = msgspec.field(name="Type", default=None)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrIssuer:
        """Deserialize a dict to this DTO."""
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
    # Flat extension fields from the badgeclass — accept raw JSON types.
    eqf: object | None = msgspec.field(name="EQF", default=None)
    ects: object | None = msgspec.field(name="ECTS", default=None)
    language: str | None = msgspec.field(name="Language", default=None)
    learning_outcome: str | None = msgspec.field(
        name="LearningOutcome", default=None
    )
    time_investment: float | None = msgspec.field(
        name="TimeInvestment", default=None
    )
    education_program_identifier: object | None = msgspec.field(
        name="EducationProgramIdentifier", default=None
    )
    # Assessment/participation flat fields.
    participation: str | None = None
    assessment_type: str | None = None
    assessment_id_verified: bool | None = None
    assessment_supervised: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrBadgeclass:
        """Deserialize a dict to this DTO."""
        return msgspec.convert(data, type=cls)


class _BadgrAwardResponse(msgspec.Struct):
    """DTO for Badgr awards API response."""

    entity_id: str | None = msgspec.field(name="id", default=None)
    name: str | None = None
    issued_on: str | None = msgspec.field(name="issuedOn", default=None)
    image: str | None = msgspec.field(name="image", default=None)
    badgeclass: _BadgrBadgeclass | None = None
    # Person/learner fields.
    given_name: str | None = None
    family_name: str | None = None
    email: str | None = None
    # Extended fields from the awards service.
    expires_at: str | None = msgspec.field(name="expires_at", default=None)
    language: str | None = msgspec.field(name="language", default=None)
    ects: object | None = msgspec.field(name="ects", default=None)
    eqf: object | None = msgspec.field(name="eqf", default=None)
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
    learning_outcome: str | None = msgspec.field(
        name="learning_outcome", default=None
    )
    education_program_identifier: object | None = msgspec.field(
        name="education_program_identifier", default=None
    )
    time_investment: float | None = msgspec.field(
        name="time_investment", default=None
    )

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> _BadgrAwardResponse:
        """Deserialize a dict to this DTO."""
        return msgspec.convert(data, type=cls)


class _BadgeclassExtensions(msgspec.Struct):
    """Typed extension values extracted from flat badgeclass fields."""

    language: str | None = None
    ects: str | None = None
    eqf: str | None = None
    learning_outcome: str | None = None
    education_program_identifier: list[str] | None = None




# Maps snake_case field names to the actual keys in originalJson (camelCase).



def _cast_to_str_list(value: object) -> list[str] | None:
    """Cast a value to list[str] | None."""
    if not isinstance(value, list):
        return None
    return [str(v) for v in value]


def _extract_extension_values(
    badgeclass: _BadgrBadgeclass | None,
) -> _BadgeclassExtensions:
    """Extract extension values from flat badgeclass fields.

    All scalar extension values are cast to strings so the credential
    output contains only string representations of the raw JSON values.
    """
    if badgeclass is None:
        return _BadgeclassExtensions()

    return _BadgeclassExtensions(
        language=(
            str(badgeclass.language)
            if badgeclass.language is not None else None
        ),
        ects=(
            str(badgeclass.ects)
            if badgeclass.ects is not None else None
        ),
        eqf=(
            str(badgeclass.eqf)
            if badgeclass.eqf is not None else None
        ),
        learning_outcome=(
            badgeclass.learning_outcome
            if isinstance(badgeclass.learning_outcome, str) else None
        ),
        education_program_identifier=(
            _cast_to_str_list(badgeclass.education_program_identifier)
            if badgeclass.education_program_identifier is not None
            else None
        ),
    )


def _credential_context_urls(
    *,
    issuer_base_url: str,
    extensions_url_prefix: str,
    badgeclass: _BadgrBadgeclass | None,
    ext_vals: _BadgeclassExtensions,
) -> list[str]:
    """Return the list of credential context URLs for non-None flat fields.

    Pure function — receives all URLs as parameters (no ``os.environ`` reads).

    Args:
        issuer_base_url: The base URL of the ec-issuer (e.g. ``http://localhost:8000``).
        extensions_url_prefix: The extensions URL prefix (e.g. ``/static/extensions``).
        badgeclass: The Badgr badgeclass DTO.
        ext_vals: Extracted extension values.

    Returns:
        List of context URLs for non-None fields.
    """
    base = issuer_base_url.rstrip("/")
    ext_dir = extensions_url_prefix
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


def _to_ob3_award(
    dto: _BadgrAwardResponse,
    *,
    issuer_base_url: str | None = None,
    extensions_url_prefix: str = "/static/extensions",
) -> OB3Award:
    """Convert a BadgrAwardResponse DTO to an OB3 Award domain model.

    Args:
        dto: The deserialized Badgr award response.
        issuer_base_url: Optional base URL to resolve relative image paths
            and credential context URLs.
        extensions_url_prefix: URL prefix for extensions (defaults to the route
            constant ``/static/extensions``).

    Returns:
        A fully-structured OB3 Award.
    """
    credential_id = _resolve_credential_id(dto)
    badge_name = _resolve_badge_name(dto)
    issuer = _resolve_issuer(dto)
    valid_from = _resolve_valid_from(dto)
    achievement_data = _resolve_achievement_data(dto)
    identifiers = _resolve_identifiers(dto)
    image = _resolve_image(dto, issuer_base_url)

    valid_to = dto.expires_at
    badgeclass = dto.badgeclass
    ext_vals = _extract_extension_values(badgeclass)

    _base_url = issuer_base_url or "http://localhost:8000"
    credential_context = _credential_context_urls(
        issuer_base_url=_base_url,
        extensions_url_prefix=extensions_url_prefix,
        badgeclass=badgeclass,
        ext_vals=ext_vals,
    )

    # Extension fields from badgeclass flat fields take priority.
    language = ext_vals.language or dto.language
    ects = ext_vals.ects or dto.ects
    eqf = ext_vals.eqf or dto.eqf
    learning_outcome = ext_vals.learning_outcome or dto.learning_outcome
    education_program_identifier = (
        ext_vals.education_program_identifier
        or dto.education_program_identifier
    )
    # Flat field from badgeclass level, fallback to dto root.
    time_investment = (
        badgeclass.time_investment if badgeclass else None
    ) or dto.time_investment

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
                time_investment=time_investment,
            ),
            identifiers=identifiers,
        ),
        credential_context=credential_context,
    )


def _resolve_issuer(dto: _BadgrAwardResponse) -> Issuer:
    """Resolve the issuer from the DTO."""
    badgeclass = dto.badgeclass
    issuer_name = ""
    issuer_type = ["Profile"]
    if badgeclass is not None and badgeclass.issuer is not None:
        issuer_id = badgeclass.issuer.entity_id or ""
        issuer_name = badgeclass.issuer.name_english or ""
        flat_type = badgeclass.issuer.type
        if flat_type:
            issuer_type = [flat_type]
    else:
        issuer_id = ""
    if not issuer_name and badgeclass is not None:
        issuer_name = badgeclass.name or ""
    return Issuer(
        id=issuer_id,
        type=issuer_type,
        name=issuer_name,
    )


def _resolve_achievement_data(dto: _BadgrAwardResponse) -> dict[str, str]:
    """Resolve achievement-level fields from the badgeclass."""
    badgeclass = dto.badgeclass
    criteria_text = ""
    description = ""
    if badgeclass is not None:
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
    """Resolve the credential ID from the ``id`` field."""
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
    """Resolve the image from the badgeclass."""
    raw_image = None
    if dto.badgeclass is not None and dto.badgeclass.image:
        raw_image = dto.badgeclass.image

    if raw_image is None:
        return None

    image_id = raw_image
    if base_url is not None and not raw_image.startswith(("http://", "https://")):
        image_id = f"{base_url.rstrip('/')}{raw_image}"

    return {"id": image_id, "type": "Image"}


def _resolve_identifiers(dto: _BadgrAwardResponse) -> list[IdentityObject]:
    """Build an identifier list from recipient data in the DTO.

    TODO: hash identity values before storing (salted SHA-256, pending team
    discussion on salt management).
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
    *,
    issuer_base_url: str | None = None,
    extensions_url_prefix: str = "/static/extensions",
) -> OB3Award:
    """Convert a Badgr API response to an OB3 Award domain model.

    Args:
        raw: The parsed JSON response from the Badgr awards API.
        issuer_base_url: Optional base URL to resolve relative image paths
            and credential context URLs.
        extensions_url_prefix: URL prefix for extensions (defaults to the
            route constant ``/static/extensions``).

    Returns:
        A fully-structured OB3 Award.
    """
    dto = _BadgrAwardResponse.from_dict(raw)
    return _to_ob3_award(
        dto,
        issuer_base_url=issuer_base_url,
        extensions_url_prefix=extensions_url_prefix,
    )