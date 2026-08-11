"""Unit tests for BadgrAwardResponse deserialization and conversion."""

from __future__ import annotations

from textwrap import dedent

import json

from src.awards.models import (
    _BadgrAwardResponse,  # pyright:ignore[reportPrivateUsage]
    _BadgrBadgeclass,  # pyright:ignore[reportPrivateUsage]
    _BadgrIssuer,  # pyright:ignore[reportPrivateUsage]
    _ob3_default_schema,  # pyright:ignore[reportPrivateUsage]
    _to_ob3_award,  # pyright:ignore[reportPrivateUsage]
    Award,
    Achievement,
    AchievementSubject,
    Criteria,
    Issuer,
)


class TestBadgrAwardResponseDeserialization:
    """Tests for deserializing Badgr API responses to DTOs."""

    def test_decode_full_response(self) -> None:
        """A full Badgr response decodes all fields correctly."""
        raw = dedent(
            """
            {
                "id": 32,
                "entity_id": "http://example.com/awards/3527",
                "name": "Teamwork Badge",
                "issued_on": "2010-01-01T00:00:00Z",
                "badgr": null,
                "revoked": false,
                "public": true,
                "grade_achieved": null,
                "expires_at": null,
                "badgeclass": {
                    "id": 18,
                    "name": "Teamwork Badge",
                    "entity_id": "http://example.com/badgeclasses/21",
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

        assert result.id == 32
        assert result.entity_id == "http://example.com/awards/3527"
        assert result.badgeclass is not None
        assert result.badgeclass.id == 18
        assert result.badgeclass.name == "Teamwork Badge"
        assert result.badgeclass.entity_id == "http://example.com/badgeclasses/21"
        assert result.badgeclass.issuer is not None
        assert result.badgeclass.issuer.name_dutch is None
        assert result.badgeclass.issuer.name_english is None
        assert result.badgeclass.issuer.faculty is None

    def test_decode_response_with_missing_fields(self) -> None:
        """A response with missing optional fields decodes correctly."""
        result = _BadgrAwardResponse.from_dict({"id": 5})

        assert result.id == 5
        assert result.entity_id is None
        assert result.name is None
        assert result.badgeclass is None

    def test_from_dict_unknown_fields_ignored(self) -> None:
        """Unknown fields in JSON are ignored."""
        result = _BadgrAwardResponse.from_dict(
            {"id": 1, "unknown_field": "ignored"}  # type: ignore[arg-type]
        )

        assert result.id == 1
        assert result.entity_id is None

    def test_from_dict_badgeclass_with_issuer(self) -> None:
        """badgeclass with issuer is properly nested."""
        raw: dict[str, object] = {
            "id": 1,
            "badgeclass": {
                "id": 10,
                "name": "Test Badge",
                "issuer": {
                    "name_dutch": "NL",
                    "name_english": "EN",
                    "faculty": "FAC",
                },
            },
        }
        result = _BadgrAwardResponse.from_dict(raw)

        assert result.badgeclass is not None
        assert result.badgeclass.id == 10
        assert result.badgeclass.name == "Test Badge"
        assert result.badgeclass.issuer is not None
        assert result.badgeclass.issuer.name_dutch == "NL"
        assert result.badgeclass.issuer.name_english == "EN"
        assert result.badgeclass.issuer.faculty == "FAC"

    def test_from_dict_badgeclass_without_issuer(self) -> None:
        """badgeclass with null/missing issuer is handled."""
        raw: dict[str, object] = {
            "id": 1,
            "badgeclass": {
                "id": 10,
                "name": "Test Badge",
                "issuer": None,
            },
        }
        result = _BadgrAwardResponse.from_dict(raw)

        assert result.badgeclass is not None
        assert result.badgeclass.issuer is None

    def test_from_dict_faculty_is_complex_object(self) -> None:
        """Faculty as a complex nested object is passed through (not parsed)."""
        raw: dict[str, object] = {
            "id": 1,
            "badgeclass": {
                "id": 10,
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
        raw_faculty: object = result.badgeclass.issuer.faculty
        assert raw_faculty is not None and isinstance(raw_faculty, dict)
        raw_inst: dict[str, object] = raw_faculty["institution"]  # pyright: ignore[reportUnknownVariableType]
        assert raw_inst["identifier"] == "university-example.org"


class TestToOb3Award:
    """Tests for _to_ob3_award conversion."""

    def test_full_response_with_mapper_fields(self) -> None:
        """Maps criteria_text, description and issuer.entity_id from badgeclass."""
        dto = _BadgrAwardResponse(
            id=2,
            entity_id="I41eovHQReGI_SG5KM6dSQ",
            name=None,
            issued_on="2021-04-20T16:20:30.521307+02:00",
            badgeclass=_BadgrBadgeclass(
                id=3,
                name="Edubadge account complete",
                entity_id="nwsL-dHyQpmvOOKBscsN_A",
                description="Complete your account to start earning badges",
                criteria_text="Register and verify your email address",
                issuer=_BadgrIssuer(
                    name_dutch="SURF Edubadges",
                    name_english="SURF Edubadges",
                    entity_id="issuer-entity-id-123",
                    faculty=None,
                ),
            ),
        )

        result = _to_ob3_award(dto)

        assert result == Award(
            id="I41eovHQReGI_SG5KM6dSQ",
            type=["VerifiableCredential", "AchievementCredential"],
            name="Edubadge account complete",
            issuer=Issuer(
                id="issuer-entity-id-123",
                type=["Profile"],
                name="Edubadge account complete",
            ),
            validFrom="2021-04-20T16:20:30.521307+02:00",
            credentialSubject=AchievementSubject(
                id="I41eovHQReGI_SG5KM6dSQ",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="I41eovHQReGI_SG5KM6dSQ",
                    type=["Achievement"],
                    criteria=Criteria(
                        narrative="Register and verify your email address",
                    ),
                    description="Complete your account to start earning badges",
                    name="Edubadge account complete",
                ),
            ),
            credentialSchema=_ob3_default_schema(),
        )

    def test_entity_id_fallback_to_string_id(self) -> None:
        """entity_id falls back to str(id) when missing."""
        dto = _BadgrAwardResponse(
            id=999,
            entity_id=None,
            name="Badge",
            issued_on="2024-01-01T00:00:00Z",
        )
        result = _to_ob3_award(dto)
        assert result.id == "999"
        assert result.credentialSubject.id == "999"
        assert result.credentialSubject.achievement.id == "999"

    def test_badge_name_fallback_to_badgeclass_name(self) -> None:
        """name falls back to badgeclass.name when missing."""
        dto = _BadgrAwardResponse(
            id=32,
            entity_id="http://example.com/awards/3527",
            name=None,
            issued_on="2010-01-01T00:00:00Z",
            badgeclass=_BadgrBadgeclass(
                id=18, name="Fallback Badge Name", entity_id=None, issuer=None
            ),
        )
        result = _to_ob3_award(dto)
        assert result.name == "Fallback Badge Name"

    def test_no_badge_name_or_badgeclass(self) -> None:
        """Badges with no name or badgeclass get empty string."""
        dto = _BadgrAwardResponse(id=1, entity_id="x", name=None, issued_on=None)
        result = _to_ob3_award(dto)
        assert result.name == ""
