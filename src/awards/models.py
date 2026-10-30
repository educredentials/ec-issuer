"""Domain models for awards (OB3 AchievementCredential)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import cast


class AssessmentTypeEnum(StrEnum):
    """Assessment type per Open Badges AssessmentTypeExtension."""

    TESTING = "testing"
    APPLICATION_OF_SKILL = "applicationOfSkill"
    PORTFOLIO = "portfolio"
    RECOGNITION_OF_PRIOR_LEARNING = "recognitionOfPriorLearning"
    PERSONALIZED_ASSESSMENT = "personalizedAssessment"
    BY_CHOICE_OF_PARTICIPANT = "byChoiceOfParticipant"

    # Allow arbitrary values from the awards service.
    @classmethod
    def _missing_(cls, value: object) -> "AssessmentTypeEnum | None":  # pyright: ignore[reportImplicitOverride]
        if isinstance(value, str):
            return cls(value)
        return None


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
    inLanguage: str | None = None
    ects: str | None = None
    eqf: str | None = None
    learningOutcome: str | None = None
    educationProgramIdentifier: list[str] | None = None
    formOfParticipation: str | None = None
    assessmentType: str | None = None
    supervisionType: str | None = None
    timeInvestment: float | None = None


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
    credential_context: list[str | dict[str, str]] | None = None
