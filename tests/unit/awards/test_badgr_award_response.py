"""Unit tests for BadgrAwardResponse deserialization and conversion."""

from __future__ import annotations

import json
from textwrap import dedent

import pytest

from src.awards.models import (
    Achievement,
    AchievementSubject,
    AwardMappingError,
    Criteria,
    Issuer,
    OB3Award,
    _BadgrAwardResponse,  # pyright:ignore[reportPrivateUsage]
    _BadgrBadgeclass,  # pyright:ignore[reportPrivateUsage]
    _BadgrFaculty,  # pyright:ignore[reportPrivateUsage]
    _BadgrIssuer,  # pyright:ignore[reportPrivateUsage]
    _ob3_default_schema,  # pyright:ignore[reportPrivateUsage]
    _resolve_identifiers,  # pyright:ignore[reportPrivateUsage]
    _to_ob3_award,  # pyright:ignore[reportPrivateUsage]
)
from src.awards.models import (
    IdentityObject as _IdentityObject,
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
