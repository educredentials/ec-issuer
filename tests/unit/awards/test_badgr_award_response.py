"""Unit tests for BadgrAwardResponse deserialization and conversion."""

from __future__ import annotations

import json
from textwrap import dedent

import pytest

from src.awards.badgr_mapping import (
    AwardMappingError,
    _BadgeclassExtensions,  # pyright:ignore[reportPrivateUsage]
    _BadgrAwardResponse,  # pyright:ignore[reportPrivateUsage]
    _BadgrBadgeclass,  # pyright:ignore[reportPrivateUsage]
    _BadgrFaculty,  # pyright:ignore[reportPrivateUsage]
    _BadgrInstitution,  # pyright:ignore[reportPrivateUsage]
    _BadgrIssuer,  # pyright:ignore[reportPrivateUsage]
    _credential_context_urls,  # pyright:ignore[reportPrivateUsage]
    _resolve_identifier,  # pyright:ignore[reportPrivateUsage]
    _resolve_issuer,  # pyright:ignore[reportPrivateUsage]
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


def _default_badgeclass(
    *,
    participation: object | None = None,
    assessment_type: object | None = None,
    language: str | None = None,
    ects: object | None = None,
    time_investment: float | None = None,
    issuer_type: str | None = None,
) -> _BadgrBadgeclass:
    """Build the standard test badgeclass used by the _to_ob3_award tests."""
    return _BadgrBadgeclass(
        name="Badge",
        entity_id="https://DOMAIN/badges/1",
        issuer=_BadgrIssuer(
            entity_id="https://DOMAIN/issuers/1",
            name_english="Issuer",
            faculty=None,
            type=issuer_type,
        ),
        participation=participation,
        assessment_type=assessment_type,
        language=language,
        ects=ects,
        time_investment=time_investment,
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
                identifier=[
                    _IdentityObject(
                        type="IdentityObject",
                        identityHash="jan@example.com",
                        identityType="emailAddress",
                        hashed=False,
                    ),
                    _IdentityObject(
                        type="IdentityObject",
                        identityHash="Jan Jansen",
                        identityType="name",
                        hashed=False,
                    ),
                ],
            ),
            credentialSchema=_ob3_default_schema(),
            validUntil=None,
            credential_context=[
                {
                    "statuslist+jwt": "https://datatracker.ietf.org/doc/draft-ietf-oauth-status-list",
                    "idx": "https://www.iana.org/assignments/jwt#idx",
                    "status": "https://www.iana.org/assignments/jwt#status",
                    "status_list": "https://www.iana.org/assignments/jwt#status_list",
                    "uri": "https://www.iana.org/assignments/jwt#uri",
                },
                "https://www.w3.org/ns/credentials/v2",
                "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
                "https://purl.imsglobal.org/spec/ob/v3p0/extensions.json",
            ],
            entity_id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
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
        identifier = result.credentialSubject.identifier
        assert len(identifier) == 2
        assert identifier[0].type == "IdentityObject"
        assert identifier[0].identityHash == "jan@example.com"
        assert identifier[0].identityType == "emailAddress"
        assert identifier[0].hashed is False
        assert identifier[1].identityHash == "Jan Jansen"
        assert identifier[1].identityType == "name"

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
        assert len(result.credentialSubject.identifier) == 1
        assert result.credentialSubject.identifier[0].identityHash == (
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
        assert len(result.credentialSubject.identifier) == 1
        assert result.credentialSubject.identifier[0].identityType == "name"

    def test_empty_identifiers_when_no_recipient_data(self) -> None:
        """No recipient data produces an empty identifiers list."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
        )
        result = _to_ob3_award(dto)
        assert result.credentialSubject.identifier == []

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
        result = _resolve_identifier(dto)
        assert len(result) == 1
        assert result[0].identityHash == "Single"


class TestCredentialContextUrls:
    """Tests for _credential_context_urls helper."""

    def test_empty_when_no_flat_fields(self) -> None:
        """Returns empty list when all flat fields are None."""
        assert _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions/v1",
            ext_vals=_BadgeclassExtensions(),
        ) == []

    def test_single_field_produces_single_url(self) -> None:
        """One non-None field produces exactly one context URL."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions/v1",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl",
                participation=["enrolment", "onsite"],
                assessmentType=["testing", "portfolio"],
            ),
        )
        assert len(urls) == 2
        assert (
            "http://localhost:8000/static/extensions/v1/ParticipationFormExtension/context.json"
            in urls
        )
        assert (
            "http://localhost:8000/static/extensions/v1/AssessmentTypeExtension/context.json"
            in urls
        )

    def test_all_flat_fields_produce_urls(self) -> None:
        """All non-None flat fields each produce a context URL."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions/v1",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl",
                ects=5,
                learningOutcome="Can do X",
                educationProgramIdentifier=["12345"],
                participation=["enrolment", "onsite"],
                assessmentType=["testing", "portfolio"],
            ),
        )
        assert len(urls) == 5
        assert "ParticipationFormExtension" in urls[0]
        assert "AssessmentTypeExtension" in urls[1]

    def test_none_fields_excluded(self) -> None:
        """Only non-None fields contribute URLs."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions/v1",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl", ects=None, participation="enrolment"
            ),
        )
        assert len(urls) == 1

    def test_url_trims_trailing_slash(self) -> None:
        """Strips trailing slash from the issuer base URL."""
        urls = _credential_context_urls(
            issuer_base_url="https://educredentials.nl/",
            extensions_url_prefix="/static/extensions/v1",
            ext_vals=_BadgeclassExtensions(participation=["enrolment"]),
        )
        assert urls == [
            "https://educredentials.nl/static/extensions/v1/ParticipationFormExtension/context.json"
        ]

    def test_url_order_matches_field_order(self) -> None:
        """Context URLs appear in the defined field order."""
        urls = _credential_context_urls(
            issuer_base_url="http://localhost:8000",
            extensions_url_prefix="/static/extensions/v1",
            ext_vals=_BadgeclassExtensions(
                inLanguage="nl",
                participation=["enrolment"],
                assessmentType=["formative"],
            ),
        )
        assert len(urls) == 2
        assert "ParticipationFormExtension" in urls[0]
        assert "AssessmentTypeExtension" in urls[1]


class TestOb3AwardWithNewFields:
    """Tests for OB3Award with extension-related fields."""

    def test_to_ob3_award_with_expires_at(self) -> None:
        """_to_ob3_award maps expires_at to validUntil."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            issued_on="2021-04-20T16:20:30.521307+02:00",
            expires_at="2024-04-20T16:20:30.521307+02:00",
            badgeclass=_default_badgeclass(),
        )
        result = _to_ob3_award(dto)
        assert result.validUntil == "2024-04-20T16:20:30.521307+02:00"

    def test_to_ob3_award_without_expires_at(self) -> None:
        """_to_ob3_award sets validUntil to None when expires_at is missing."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            expires_at=None,
            badgeclass=_default_badgeclass(),
        )
        result = _to_ob3_award(dto)
        assert result.validUntil is None

    def test_to_ob3_award_with_flat_field_extensions(self) -> None:
        """_to_ob3_award moves flat extension fields onto Achievement."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            expires_at="2025-01-01T00:00:00Z",
            badgeclass=_default_badgeclass(
                participation=["enrolment", "onsite"],
                assessment_type=["summative", "formative"],
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
        assert ach.assessmentType == ["summative", "formative"]
        assert ach.formOfParticipation == ["enrolment", "onsite"]
        # 4 flat fields producing context: participation, assessment_type, ects,
        #   time_investment. inLanguage is native OB3 — no extension URL.
        # 1 inline dict + 4 extension URLs + 3 base OB3 contexts
        assert result.credential_context is not None
        assert len(result.credential_context) == 8

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
            badgeclass=_default_badgeclass(issuer_type="Organization"),
        )
        result = _to_ob3_award(dto)
        assert result.issuer.type == ["Organization"]

    def test_to_ob3_award_issuer_type_fallback(self) -> None:
        """_resolve_issuer falls back to Profile when Type is missing."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_default_badgeclass(),
        )
        result = _to_ob3_award(dto)
        assert result.issuer.type == ["Profile"]

    def test_to_ob3_award_assessment_fields_produce_context_urls(self) -> None:
        """_to_ob3_award includes assessment-related context URLs when flat
        fields are set."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_default_badgeclass(
                participation=["online", "onsite"],
                assessment_type=["summative", "formative"],
            ),
        )
        result = _to_ob3_award(dto)
        ach = result.credentialSubject.achievement
        assert ach.assessmentType == ["summative", "formative"]
        assert ach.formOfParticipation == ["online", "onsite"]
        assert result.credential_context is not None
        # First item is inline JSON-LD context, remaining are extension URLs
        assert isinstance(result.credential_context[0], dict)
        assert result.credential_context[0]["assessmentType"] == "https://w3id.org/openbadges/extensions#assessmentType"
        assert result.credential_context[0]["formOfParticipation"] == "https://w3id.org/openbadges/extensions#formOfParticipation"
        # 1 inline dict + 2 extension URLs + 3 base OB3 contexts
        assert len(result.credential_context) == 6

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

    # --- parentOrg tests ---

    def test_resolve_issuer_populates_parent_org_from_faculty_institution(
        self,
    ) -> None:
        """_resolve_issuer builds parentOrg from faculty.institution data."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/eshcc",
                    name_english="Erasmus School of History",
                    faculty=_BadgrFaculty(
                        entity_id="https://ror.org/57197",
                        institution=_BadgrInstitution(
                            name_english="Erasmus University Rotterdam",
                            country_code="NL",
                            identifier="eur.nl",
                            brin="21PE",
                        ),
                    ),
                ),
            ),
        )

        result = _resolve_issuer(dto)

        assert result.id == "https://DOMAIN/issuers/eshcc"
        assert result.name == "Erasmus School of History"
        assert result.parentOrg is not None
        assert result.parentOrg.id == "https://ror.org/57197"
        assert result.parentOrg.name == "Erasmus University Rotterdam"
        assert result.parentOrg.address is not None
        assert result.parentOrg.address.addressCountryCode == "NL"
        assert len(result.parentOrg.otherIdentifier) == 2

    def test_resolve_issuer_preserves_issuer_type_from_flat_field(
        self,
    ) -> None:
        """_resolve_issuer keeps the flat Type field on the issuer."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    type="Organization",
                ),
            ),
        )

        result = _resolve_issuer(dto)
        assert result.type == ["Organization"]

    def test_resolve_issuer_with_country_code_and_identifiers(
        self,
    ) -> None:
        """parentOrg contains country code and both BRIN/SCHAC identifiers."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=_BadgrFaculty(
                        entity_id="https://ror.org/12345",
                        institution=_BadgrInstitution(
                            name_english="Test University",
                            country_code="DE",
                            identifier="test.de",
                            brin="AB12",
                        ),
                    ),
                ),
            ),
        )

        result = _resolve_issuer(dto)
        assert result.parentOrg is not None
        assert result.parentOrg.address is not None
        assert result.parentOrg.address.addressCountryCode == "DE"
        assert result.parentOrg.otherIdentifier[0].identifier == "AB12"
        assert result.parentOrg.otherIdentifier[0].identifierType == "ext:BRIN"
        assert result.parentOrg.otherIdentifier[1].identifier == "test.de"
        assert result.parentOrg.otherIdentifier[1].identifierType == "ext:SCHAC"

    def test_resolve_issuer_with_only_schac_or_brin(self) -> None:
        """parentOrg.otherIdentifier includes only present identifiers."""
        # Only SCHAC
        dto_schac = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=_BadgrFaculty(
                        institution=_BadgrInstitution(
                            identifier="schac.example.org",
                        ),
                    ),
                ),
            ),
        )
        result_schac = _resolve_issuer(dto_schac)
        assert len(result_schac.parentOrg.otherIdentifier) == 1
        assert result_schac.parentOrg.otherIdentifier[0].identifierType == "ext:SCHAC"

        # Only BRIN
        dto_brin = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/1",
            issued_on="2024-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                name="Badge",
                entity_id="https://DOMAIN/badges/1",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/1",
                    name_english="Issuer",
                    faculty=_BadgrFaculty(
                        institution=_BadgrInstitution(
                            brin="BR1N99",
                        ),
                    ),
                ),
            ),
        )
        result_brin = _resolve_issuer(dto_brin)
        assert len(result_brin.parentOrg.otherIdentifier) == 1
        assert result_brin.parentOrg.otherIdentifier[0].identifierType == "ext:BRIN"

    def test_to_ob3_award_with_parent_org(self) -> None:
        """_to_ob3_award produces a full OB3 award with parentOrg."""
        dto = _BadgrAwardResponse(
            entity_id="https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            issued_on="2021-04-20T16:20:30.521307+02:00",
            given_name="Jan",
            family_name="Jansen",
            email="jan@example.com",
            badgeclass=_BadgrBadgeclass(
                name="Edubadge account complete",
                entity_id="https://DOMAIN/badges/nwsL-dHyQpmvOOKBscsN_A",
                description="Complete your account",
                criteria_text="Register and verify email",
                issuer=_BadgrIssuer(
                    entity_id="https://DOMAIN/issuers/eshcc",
                    name_english="Erasmus School of History",
                    faculty=_BadgrFaculty(
                        entity_id="https://ror.org/57197",
                        institution=_BadgrInstitution(
                            name_english="Erasmus University Rotterdam",
                            country_code="NL",
                            identifier="eur.nl",
                            brin="21PE",
                        ),
                    ),
                ),
            ),
        )
        result = _to_ob3_award(dto)
        assert result.issuer.parentOrg is not None
        assert result.issuer.parentOrg.id == "https://ror.org/57197"
        assert result.issuer.parentOrg.name == "Erasmus University Rotterdam"
        assert result.issuer.parentOrg.address is not None
        assert result.issuer.parentOrg.address.addressCountryCode == "NL"
        assert len(result.issuer.parentOrg.otherIdentifier) == 2
