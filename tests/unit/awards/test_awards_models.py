"""Unit tests for award conversion functions (models module).

Tests the data flow from raw Badgr API JSON through DTOs to OB3Award and EDCAward
domain models. Covers edge cases: missing fields, None badgeclass, fallback chains.
"""

from src.awards.models import (
    EDCAward,
    OB3Award,
    _BadgrAwardResponse,  # pyright:ignore[reportPrivateUsage]
    _resolve_badge_name,  # pyright:ignore[reportPrivateUsage]
    _resolve_entity_id,  # pyright:ignore[reportPrivateUsage]
    _resolve_valid_from,  # pyright:ignore[reportPrivateUsage]
    edc_award_from_badgr_api_response,
    ob3_award_from_badgr_api_response,
)

# Minimal valid Badgr award response with all fields populated.
_VALID_BADGR_RESPONSE = {
    "id": 42,
    "entity_id": "http://example.com/awards/42",
    "name": "Teamwork Badge",
    "issued_on": "2024-06-15T10:00:00Z",
    "badgeclass": {
        "id": 18,
        "name": "Teamwork Badge",
        "entity_id": "http://example.com/badgeclasses/18",
        "description": "Demonstrates teamwork ability",
        "criteria_text": "Complete the project",
        "issuer": {
            "name_dutch": "Test NL",
            "name_english": "Test Corp",
            "entity_id": "http://example.com/issuers/1",
        },
    },
    "given_name": "Jan",
    "family_name": "Jansen",
}

# Bare-minimum response: only `id` is required by the DTO.
_MINIMAL_BADGR_RESPONSE = {"id": 1}


class TestResolveEntityId:
    """Tests for the _resolve_entity_id helper."""

    def test_returns_entity_id_when_present(self):
        """_resolve_entity_id returns dto.entity_id when set."""
        dto = _BadgrAwardResponse.from_dict(_VALID_BADGR_RESPONSE)
        assert _resolve_entity_id(dto) == "http://example.com/awards/42"

    def test_fallback_to_str_id_when_entity_id_missing(self):
        """_resolve_entity_id falls back to str(dto.id) when entity_id is None."""
        dto = _BadgrAwardResponse.from_dict({"id": 99})
        assert _resolve_entity_id(dto) == "99"


class TestResolveBadgeName:
    """Tests for the _resolve_badge_name helper."""

    def test_returns_dto_name_when_present(self):
        """_resolve_badge_name returns dto.name when set."""
        dto = _BadgrAwardResponse.from_dict(_VALID_BADGR_RESPONSE)
        assert _resolve_badge_name(dto) == "Teamwork Badge"

    def test_fallback_to_badgeclass_name(self):
        """_resolve_badge_name falls back to badgeclass.name when dto.name is None."""
        dto = _BadgrAwardResponse.from_dict(
            {"id": 1, "name": None, "badgeclass": {"id": 1, "name": "Badge B"}}
        )
        assert _resolve_badge_name(dto) == "Badge B"

    def test_returns_empty_string_when_no_name_anywhere(self):
        """_resolve_badge_name returns '' when no name source is present."""
        dto = _BadgrAwardResponse.from_dict({"id": 1, "name": None, "badgeclass": None})
        assert _resolve_badge_name(dto) == ""


class TestResolveValidFrom:
    """Tests for the _resolve_valid_from helper."""

    def test_returns_issued_on_when_present(self):
        """_resolve_valid_from returns dto.issued_on when set."""
        dto = _BadgrAwardResponse.from_dict(_VALID_BADGR_RESPONSE)
        assert _resolve_valid_from(dto) == "2024-06-15T10:00:00Z"

    def test_returns_empty_string_when_issued_on_missing(self):
        """_resolve_valid_from returns '' when dto.issued_on is None."""
        dto = _BadgrAwardResponse.from_dict({"id": 1, "issued_on": None})
        assert _resolve_valid_from(dto) == ""


class TestOb3AwardFromBadgrApi:
    """Tests for ob3_award_from_badgr_api_response."""

    def test_produces_valid_ob3_award(self):
        """Full response produces an OB3Award with all fields populated."""
        award = ob3_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert isinstance(award, OB3Award)
        assert award.id == "http://example.com/awards/42"
        assert award.name == "Teamwork Badge"
        assert award.validFrom == "2024-06-15T10:00:00Z"
        assert award.credentialSubject.achievement.name == "Teamwork Badge"
        assert award.credentialSubject.achievement.description == (
            "Demonstrates teamwork ability"
        )

    def test_handles_minimal_response(self):
        """Minimal response produces an OB3Award with fallback defaults."""
        award = ob3_award_from_badgr_api_response(_MINIMAL_BADGR_RESPONSE)
        assert isinstance(award, OB3Award)
        assert award.id == "1"
        assert award.name == ""
        assert award.validFrom == ""


class TestEdcAwardFromBadgrApi:
    """Tests for edc_award_from_badgr_api_response."""

    def test_produces_valid_edc_award(self):
        """Full response produces an EDCAward with all required fields."""
        award = edc_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert isinstance(award, EDCAward)
        assert award.given_name == "Jan"
        assert award.family_name == "Jansen"
        assert award.valid_from == "2024-06-15T10:00:00Z"
        assert award.learning_achievement["name"] == "Teamwork Badge"
        assert award.learning_achievement["description"] == (
            "Demonstrates teamwork ability"
        )
        assert award.learning_achievement["type"] == "achievement"
        assert award.awarding_body["name"] == "Test Corp"
        assert award.awarding_body["id"] == "http://example.com/issuers/1"
        assert award.awarding_body["type"] == (
            "http://publications.europa.eu/ontology/authority#Authority"
        )
        assert award.credential_schema == {
            "id": "http://data.europa.eu/snb/credential/25831c2",
            "type": "sd-jwt_vc+json",
        }

    def test_handles_minimal_response(self):
        """Minimal response produces an EDCAward with empty-string defaults."""
        award = edc_award_from_badgr_api_response(_MINIMAL_BADGR_RESPONSE)
        assert isinstance(award, EDCAward)
        assert award.given_name == ""
        assert award.family_name == ""
        assert award.valid_from == ""
        assert award.learning_achievement["name"] == ""
        assert award.awarding_body["id"] == ""
        assert award.subject_id == "1"

    def test_falls_back_to_dutch_issuer_name(self):
        """_to_edc_award prefers English, falls back to Dutch when English is None."""
        response = {
            "id": 5,
            "entity_id": "http://example.com/awards/5",
            "name": "Dutch Badge",
            "badgeclass": {
                "id": 2,
                "name": "Dutch Badge",
                "issuer": {
                    "name_dutch": "Test NL",
                    "name_english": None,
                },
            },
        }
        award = edc_award_from_badgr_api_response(response)
        assert award.awarding_body["name"] == "Test NL"
