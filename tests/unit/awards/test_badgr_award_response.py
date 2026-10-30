"""Unit tests for BadgrAwardResponse deserialization and conversion."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from textwrap import dedent

import pytest

from src.awards.badgr_mapping import (
    AwardMappingError,
    _BadgeclassExtensions,  # pyright:ignore[reportPrivateUsage]
    _BadgrAwardResponse,  # pyright:ignore[reportPrivateUsage]
    _BadgrBadgeclass,  # pyright:ignore[reportPrivateUsage]
    _BadgrFaculty,  # pyright:ignore[reportPrivateUsage]
    _BadgrIssuer,  # pyright:ignore[reportPrivateUsage]
    _credential_context_urls,  # pyright:ignore[reportPrivateUsage]
    _resolve_identifiers,  # pyright:ignore[reportPrivateUsage]
    _to_ob3_award,  # pyright:ignore[reportPrivateUsage]
    ob3_award_from_badgr_api_response,
)
from src.awards.models import (
    Achievement,
    AchievementSubject,
    Criteria,
    IdentityObject as _IdentityObject,
    Issuer,
    OB3Award,
    _ob3_default_schema,  # pyright:ignore[reportPrivateUsage]
)


class TestBadgrAwardResponseDeserialization:
    """Tests for deserializing Badgr API responses to DTOs."""

    def test_decode_full_response(self) -> None:
        """A full Badgr response decodes all fields correctly."""
        raw = dedent(
            """
            {
                "id": "https://DOMAIN/assertions/3527",
                "name": "Teamwork Badge",
                "issued_on": "2010-01-01T00:00:00Z",
                "badgr": null,
                "revoked": false,
                "public": true,
                "grade_achieved": null,
                "expires_at": null,
                "badgeclass": {
                    "id": "https://DOMAIN/badges/21",
                    "name": "Teamwork Badge",
                    "issuer": {
                        "name_dutch": null,
                        "name_english": null,
                        "faculty": null
                    }
                }
            }
            """
        ).strip()

        result = _BadgrAwardResponse.from_dict(json.loads(raw))  # pyright: ignore[reportAny]

        assert result.entity_id == "https://DOMAIN/assertions/3527"
        assert result.badgeclass is not None
        assert result.badgeclass.name == "Teamwork Badge"
        assert result.badgeclass.entity_id == "https://DOMAIN/badges/21"
        assert result.badgeclass.issuer is not None
        assert result.badgeclass.issuer.name_dutch is None
        assert result.badgeclass.issuer.name_english is None
        assert result.badgeclass.issuer.faculty is None

    def test_decode_response_with_missing_fields(self) -> None:
        """A response with missing optional fields decodes correctly."""
        result = _BadgrAwardResponse.from_dict({})

        assert result.entity_id is None
        assert result.name is None
        assert result.badgeclass is None

    def test_from_dict_unknown_fields_ignored(self) -> None:
        """Unknown fields in JSON are ignored."""
        result = _BadgrAwardResponse.from_dict(
            {"unknown_field": "ignored"}  # type: ignore[arg-type]
        )

        assert result.entity_id is None

    def test_from_dict_badgeclass_with_issuer(self) -> None:
        """badgeclass with issuer is properly nested."""
        raw: dict[str, object] = {
            "badgeclass": {
                "name": "Test Badge",
                "issuer": {
                    "name_dutch": "NL",
                    "name_english": "EN",
                    "faculty": {
                        "name_dutch": "FAC_NL",
                        "name_english": "FAC_EN",
                    },
                },
            },
        }
        result = _BadgrAwardResponse.from_dict(raw)

        assert result.badgeclass is not None
        assert result.badgeclass.name == "Test Badge"
        assert result.badgeclass.issuer is not None
        assert result.badgeclass.issuer.name_dutch == "NL"
        assert result.badgeclass.issuer.name_english == "EN"
        assert result.badgeclass.issuer.faculty is not None
        assert result.badgeclass.issuer.faculty.name_dutch == "FAC_NL"
        assert result.badgeclass.issuer.faculty.name_english == "FAC_EN"

    def test_from_dict_badgeclass_without_issuer(self) -> None:
        """badgeclass with null/missing issuer is handled."""
        raw: dict[str, object] = {
            "badgeclass": {
                "name": "Test Badge",
                "issuer": None,
            },
        }
        result = _BadgrAwardResponse.from_dict(raw)

        assert result.badgeclass is not None
        assert result.badgeclass.issuer is None

    def test_from_dict_faculty_is_complex_object(self) -> None:
        """Faculty as a complex nested object is parsed into DTOs."""
        raw: dict[str, object] = {
            "badgeclass": {
                "name": "Test Badge",
                "issuer": {
                    "name_dutch": "SURF Edubadges",
                    "name_english": "SURF Edubadges",
                    "faculty": {
                        "name_dutch": "SURF",
                        "name_english": "SURF",
                        "institution": {
                            "name_dutch": "University Voorbeeld",
                            "identifier": "university-example.org",
                        },
                    },
                },
            },
        }
        result = _BadgrAwardResponse.from_dict(raw)

        assert result.badgeclass is not None
        assert result.badgeclass.issuer is not None
        faculty = result.badgeclass.issuer.faculty
        assert faculty is not None and isinstance(faculty, _BadgrFaculty)
        assert faculty.institution is not None
        assert faculty.institution.name_dutch == "University Voorbeeld"
        assert faculty.institution.identifier == "university-example.org"


class TestToOb3Award:
    """Tests for _to_ob3_award conversion."""

    def test_full_response_with_mapper_fields(self) -> None:
        """Maps criteria_text, description, issuer.entity_id and identifiers."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            name=None,
            issued_on="2021-04-20T16:20:30.521307+02:00",
            given_name="Jan",
            family_name="Jansen",
            email="jan@example.com",
            badgeclass=_BadgrBadgeclass(
                name="Edubadge account complete",
                entity_id="https://DOMAIN/badges/nwsL-dHyQpmvOOKBscsN_A",
                description="Complete your account to start earning badges",
                criteria_text="Register and verify your email address",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/issuer-entity-id-123",
                    name_dutch="SURF Edubadges",
                    name_english="SURF Edubadges",
                    faculty=None,
                ),
            ),
        )

        result = _to_ob3_award(dto)

        assert result == OB3Award(
            id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Edubadge account complete",
            issuer=Issuer(
                id="https://DOMAIN/issuers/issuer-entity-id-123",
                type=["Profile"],
                name="SURF Edubadges",
            ),
            validFrom="2021-04-20T16:20:30.521307+02:00",
            credentialSubject=AchievementSubject(
                id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
                    type=["Achievement"],
                    criteria=Criteria(
                        narrative="Register and verify your email address",
                    ),
                    description="Complete your account to start earning badges",
                    name="Edubadge account complete",
                    inLanguage=None,
                    ects=None,
                    eqf=None,
                    learningOutcome=None,
                    educationProgramIdentifier=None,
                    formOfParticipation=None,
                    assessmentType=None,
                    timeInvestment=None,
                ),
                identifiers=[
                    _IdentityObject(
                        type=["IdentityObject"],
                        identityHash="jan@example.com",
                        identityType="emailAddress",
                        hashed=False,
                    ),
                    _IdentityObject(
                        type=["IdentityObject"],
                        identityHash="Jan Jansen",
                        identityType="name",
                        hashed=False,
                    ),
                ],
            ),
            credentialSchema=_ob3_default_schema(),
            validUntil=None,
            credential_context=[],
        )

    def test_raises_when_entity_id_missing(self) -> None:
        """_to_ob3_award raises AwardMappingError when @id is missing."""
        dto = _BadgrAwardResponse(
            entity_id=None,
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
        )
        with pytest.raises(AwardMappingError, match="missing 'id'"):
            _ = _to_ob3_award(dto)

    def test_badge_name_fallback_to_badgeclass_name(self) -> None:
        """name falls back to badgeclass.name when missing."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            name=None,
            issued_on="2010-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Fallback Badge Name", entity_id=None, issuer=None
            ),
        )
        result = _to_ob3_award(dto)
        assert result.name == "Fallback Badge Name"

    def test_no_badge_name_or_badgeclass(self) -> None:
        """Badges with no name or badgeclass get empty string."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1", name=None, issued_on=None
        )
        result = _to_ob3_award(dto)
        assert result.name == ""

    def test_identifiers_populated_with_email_and_name(self) -> None:
        """dto with given_name, family_name, and email produces two identifiers."""
        dto = _BadgrAwardResponse(
            entity_id="http://example.com/awards/1",
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
            given_name="Jan",
            family_name="Jansen",
            email="jan@example.com",
        )
        result = _to_ob3_award(dto)
        identifiers = result.credentialSubject.identifiers
        assert len(identifiers) == 2
        assert identifiers[0].type == ["IdentityObject"]
        assert identifiers[0].identityHash == "jan@example.com"
        assert identifiers[0].identityType == "emailAddress"
        assert identifiers[0].hashed is False
        assert identifiers[1].identityHash == "Jan Jansen"
        assert identifiers[1].identityType == "name"

    def test_identifiers_only_email_when_no_name(self) -> None:
        """Only an emailAddress identifier is produced when no name fields exist."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
            given_name=None,
            family_name=None,
            email="solo@example.com",
        )
        result = _to_ob3_award(dto)
        assert len(result.credentialSubject.identifiers) == 1
        assert result.credentialSubject.identifiers[0].identityHash == (
            "solo@example.com"
        )

    def test_identifiers_only_name_when_no_email(self) -> None:
        """Only a name identifier is produced when email is missing."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
            given_name="M",
            family_name="L",
            email=None,
        )
        result = _to_ob3_award(dto)
        assert len(result.credentialSubject.identifiers) == 1
        assert result.credentialSubject.identifiers[0].identityType == "name"

    def test_empty_identifiers_when_no_recipient_data(self) -> None:
        """No recipient data produces an empty identifiers list."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
        )
        result = _to_ob3_award(dto)
        assert result.credentialSubject.identifiers == []

    def test_name_parts_filtered_for_none(self) -> None:
        """Only non-None name parts are joined."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
            given_name="Single",
            family_name=None,
            email=None,
        )
        result = _resolve_identifiers(dto)
        assert len(result) == 1
        assert result[0].identityHash == "Single"


@contextmanager
def _patch_env(key: str, value: str):
    """Temporarily set an environment variable and restore on exit."""
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            _ = os.environ.pop(key, None)
        else:
            os.environ[key] = old


class TestCredentialContextUrls:
    """Tests for _credential_context_urls helper."""

    def _make_ext(self, **kwargs: object) -> _BadgeclassExtensions:
        """Build a _BadgeclassExtensions from kwargs."""
        _inLanguage = kwargs.get("inLanguage")
        _ects = kwargs.get("ects")
        _eqf = kwargs.get("eqf")
        _learningOutcome = kwargs.get("learningOutcome")
        _educationProgramIdentifier = kwargs.get("educationProgramIdentifier")
        return _BadgeclassExtensions(
            inLanguage=str(_inLanguage) if _inLanguage is not None else None,
            ects=float(_ects) if isinstance(_ects, (int, float)) else None,
            eqf=int(_eqf) if isinstance(_eqf, int) else None,
            learningOutcome=(
                _learningOutcome if isinstance(_learningOutcome, str) else None
            ),
            educationProgramIdentifier=(
                [str(v) for v in _educationProgramIdentifier]
                if isinstance(_educationProgramIdentifier, list)
                else None
            ),
        )

    def test_empty_when_no_flat_fields(self) -> None:
        """Returns empty list when all flat fields are None."""
        assert _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions",
            ext_vals=_BadgeclassExtensions(),
        ) == []

    def test_single_field_produces_single_url(self) -> None:
        """One non-None field produces exactly one context URL."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl", participation="enrolment"
            ),
        )
        assert len(urls) == 1
        assert (
            "http://localhost:8000/static/extensions/ParticipationFormExtension/context.json"
            in urls
        )

    def test_all_flat_fields_produce_urls(self) -> None:
        """All non-None flat fields each produce a context URL."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl",
                ects=5,
                learningOutcome="Can do X",
                educationProgramIdentifier=["12345"],
                participation="enrolment",
                assessmentType="formative",
            ),
        )
        assert len(urls) == 5

    def test_none_fields_excluded(self) -> None:
        """Only non-None fields contribute URLs."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl", ects=None, participation="enrolment"
            ),
        )
        assert len(urls) == 1

    def test_url_uses_env_var_when_set(self) -> None:
        """Uses EC_ISSUER_URL env var when available."""
        with _patch_env("EC_ISSUER_URL", "https://educredentials.nl"):
            urls = _credential_context_urls(
                issuer_base_url="https://educredentials.nl",
                extensions_url_prefix="/static/extensions",
                ext_vals=_BadgeclassExtensions(participation="enrolment"),
            )
        assert len(urls) == 1
        assert urls[0] == "https://educredentials.nl/static/extensions/ParticipationFormExtension/context.json"

    def test_url_trims_trailing_slash(self) -> None:
        """Strips trailing slash from public URL."""
        with _patch_env("EC_ISSUER_URL", "https://educredentials.nl/"):
            urls = _credential_context_urls(
                issuer_base_url="https://educredentials.nl",
                extensions_url_prefix="/static/extensions",
                ext_vals=_BadgeclassExtensions(participation="enrolment"),
            )
        assert len(urls) == 1
        assert urls[0] == "https://educredentials.nl/static/extensions/ParticipationFormExtension/context.json"

    def test_url_order_matches_field_order(self) -> None:
        """Context URLs appear in the defined field order."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl", participation="enrolment", assessmentType="formative"
            ),
        )
        assert len(urls) == 2
        assert "ParticipationFormExtension" in urls[0]
        assert "AssessmentTypeExtension" in urls[1]


class TestOb3AwardWithNewFields:
    """Tests for OB3Award with extension-related fields."""

    def test_ob3_award_with_valid_to(self) -> None:
        """OB3Award can be constructed with validUntil set."""
        award = OB3Award(
            id="https://DOMAIN/assertions/1",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Badge",
            issuer=Issuer(
                id="https://DOMAIN/issuers/1", type=["Profile"], name="Issuer"
            ),
            validFrom="2024-01-01T00:00:00Z",
            validUntil="2025-01-01T00:00:00Z",
            credentialSubject=AchievementSubject(
                id="https://DOMAIN/assertions/1",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://DOMAIN/assertions/1",
                    type=["Achievement"],
                    criteria=Criteria(narrative="Complete the badge"),
                    description="Badge for completing the task",
                    name="Badge",
                ),
            ),
            credential_context=[],
        )
        assert award.validUntil == "2025-01-01T00:00:00Z"

    def test_ob3_award_with_credential_context(self) -> None:
        """OB3Award can hold credential_context list."""
        context_urls = [
            "https://educredentials.nl/static/extensions/ECTSExtension/context.json",
        ]
        award = OB3Award(
            id="https://DOMAIN/assertions/1",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Badge",
            issuer=Issuer(
                id="https://DOMAIN/issuers/1", type=["Profile"], name="Issuer"
            ),
            validFrom="2024-01-01T00:00:00Z",
            credential_context=context_urls,
            credentialSubject=AchievementSubject(
                id="https://DOMAIN/assertions/1",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://DOMAIN/assertions/1",
                    type=["Achievement"],
                    criteria=Criteria(narrative="Complete the badge"),
                    description="Badge for completing the task",
                    name="Badge",
                ),
            ),
        )
        assert award.credential_context == context_urls

    def test_ob3_award_with_valid_in_language(self) -> None:
        """OB3Award can hold inLanguage field."""
        award = OB3Award(
            id="https://DOMAIN/assertions/1",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Badge",
            issuer=Issuer(
                id="https://DOMAIN/issuers/1", type=["Profile"], name="Issuer"
            ),
            validFrom="2024-01-01T00:00:00Z",
            credentialSubject=AchievementSubject(
                id="https://DOMAIN/assertions/1",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://DOMAIN/assertions/1",
                    type=["Achievement"],
                    criteria=Criteria(narrative="Complete the badge"),
                    description="Badge for completing the task",
                    name="Badge",
                    inLanguage="nl",
                ),
            ),
        )
        assert award.credentialSubject.achievement.inLanguage == "nl"

    def test_ob3_award_with_ECTS(self) -> None:
        """OB3Award can hold ects field."""
        award = OB3Award(
            id="https://DOMAIN/assertions/1",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Badge",
            issuer=Issuer(
                id="https://DOMAIN/issuers/1", type=["Profile"], name="Issuer"
            ),
            validFrom="2024-01-01T00:00:00Z",
            credentialSubject=AchievementSubject(
                id="https://DOMAIN/assertions/1",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://DOMAIN/assertions/1",
                    type=["Achievement"],
                    criteria=Criteria(narrative="Complete the badge"),
                    description="Badge for completing the task",
                    name="Badge",
                    ects=5,
                ),
            ),
        )
        assert award.credentialSubject.achievement.ects == 5

    def test_ob3_award_with_assessment_fields(self) -> None:
        """OB3Award can hold assessment type, id_verified, and supervised fields."""
        award = OB3Award(
            id="https://DOMAIN/assertions/1",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Badge",
            issuer=Issuer(
                id="https://DOMAIN/issuers/1", type=["Profile"], name="Issuer"
            ),
            validFrom="2024-01-01T00:00:00Z",
            credentialSubject=AchievementSubject(
                id="https://DOMAIN/assertions/1",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://DOMAIN/assertions/1",
                    type=["Achievement"],
                    criteria=Criteria(narrative="Complete the badge"),
                    description="Badge for completing the task",
                    name="Badge",
                    assessmentType="formative",
                ),
            ),
        )
        assert award.credentialSubject.achievement.assessmentType == "formative"

    def test_to_ob3_award_with_expires_at(self) -> None:
        """_to_ob3_award maps expires_at to validUntil."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            issued_on="2021-04-20T16:20:30.521307+02:00",
            expires_at="2024-04-20T16:20:30.521307+02:00",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=None,
                ),
            ),
        )
        result = _to_ob3_award(dto)
        assert result.validUntil == "2024-04-20T16:20:30.521307+02:00"

    def test_to_ob3_award_without_expires_at(self) -> None:
        """_to_ob3_award sets validUntil to None when expires_at is missing."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            expires_at=None,
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=None,
                ),
            ),
        )
        result = _to_ob3_award(dto)
        assert result.validUntil is None

    def test_to_ob3_award_with_flat_field_extensions(self) -> None:
        """_to_ob3_award moves flat extension fields onto Achievement."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            expires_at="2025-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=None,
                ),
                participation="enrolment",
                assessment_type="summative",
                language="nl",
                ects="5",
                time_investment=42.0,
            ),
        )
        result = _to_ob3_award(dto)
        ach = result.credentialSubject.achievement
        assert result.validUntil == "2025-01-01T00:00:00Z"
        assert ach.inLanguage == "nl"
        assert ach.ects == "5"
        assert ach.timeInvestment == "42.0"
        assert ach.assessmentType == "summative"
        assert ach.formOfParticipation == "enrolment"
        # 4 flat fields producing context: participation, assessment_type, ects,
        #   time_investment. inLanguage is native OB3 — no extension URL.
        assert result.credential_context is not None
        assert len(result.credential_context) == 4

    def test_to_ob3_award_time_investment_from_raw_json(self) -> None:
        """time_investment flows from flat JSON field through to Achievement."""
        raw: dict[str, object] = {
            "id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/1",
                "name": "Badge",
                "issuer": {
                    "id": "https://DOMAIN/issuers/1",
                    "name": {"en": "Issuer"},
                },
                "TimeInvestment": 25.5,
            },
        }
        result = ob3_award_from_badgr_api_response(raw, issuer_base_url="https://DOMAIN")
        assert result.credentialSubject.achievement.timeInvestment == "25.5"
        assert result.validFrom == "2024-01-01T00:00:00Z"

    def test_to_ob3_award_issuer_type_from_flat_field(self) -> None:
        """_resolve_issuer uses the flat Type field from _BadgrIssuer."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=None,
                    type="Organization",
                ),
            ),
        )
        result = _to_ob3_award(dto)
        assert result.issuer.type == ["Organization"]

    def test_to_ob3_award_issuer_type_fallback(self) -> None:
        """_resolve_issuer falls back to Profile when Type is missing."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=None,
                ),
            ),
        )
        result = _to_ob3_award(dto)
        assert result.issuer.type == ["Profile"]

    def test_to_ob3_award_assessment_fields_produce_context_urls(self) -> None:
        """_to_ob3_award includes assessment-related context URLs when flat
        fields are set."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=None,
                ),
                assessment_type="summative",
            ),
        )
        result = _to_ob3_award(dto)
        ach = result.credentialSubject.achievement
        assert ach.assessmentType == "summative"
        assert result.credential_context is not None
        assert len(result.credential_context) == 1

    def test_extensions_from_raw_json(self) -> None:
        """_extract_extension_values works when data arrives via msgspec from
        raw JSON (simulating the real API flow)."""
        raw: dict[str, object] = {
            "id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "expiresAt": "2025-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/1",
                "name": "Badge",
                "issuer": {
                    "id": "https://DOMAIN/issuers/1",
                    "name": {
                        "en": "Issuer",
                    },
                },
                "Language": "nl_NL",
                "EducationProgramIdentifier": ["56823"],
            },
        }
        result = ob3_award_from_badgr_api_response(raw, issuer_base_url="https://DOMAIN")
        ach = result.credentialSubject.achievement
        assert ach.inLanguage == "nl-NL"
        assert ach.educationProgramIdentifier == ["56823"]
        assert result.validFrom == "2024-01-01T00:00:00Z"

    def test_criteria_narrative_from_nested_criteria(self) -> None:
        """criteria.narrative is extracted from badgeclass.criteria."""
        raw = {
            "id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/1",
                "name": "Badge",
                "issuer": {
                    "id": "https://DOMAIN/issuers/1",
                    "name": {
                        "en": "Issuer",
                    },
                },
                "criteria": {
                    "narrative": (
                        "Will appreciate the benefits of learning "
                        "a foreign language."
                    ),
                },
            },
        }
        result = ob3_award_from_badgr_api_response(raw, issuer_base_url="https://DOMAIN")
        ach = result.credentialSubject.achievement
        assert ach.criteria.narrative == (
            "Will appreciate the benefits of learning a foreign language."
        )
        assert result.validFrom == "2024-01-01T00:00:00Z"
