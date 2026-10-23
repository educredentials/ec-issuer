"""Unit tests for award conversion functions (models module).

Tests the data flow from raw Badgr API JSON through DTOs to OB3Award
domain models. Covers edge cases: missing fields, None badgeclass, fallback chains.
"""

import pytest

from src.awards.models import (
    AwardMappingError,
    OB3Award,
    _BadgrAwardResponse,  # pyright:ignore[reportPrivateUsage]
    _resolve_badge_name,  # pyright:ignore[reportPrivateUsage]
    _resolve_credential_id,  # pyright:ignore[reportPrivateUsage]
    _resolve_valid_from,  # pyright:ignore[reportPrivateUsage]
    ob3_award_from_badgr_api_response,
)

# Minimal valid Badgr award response with all fields populated.
_VALID_BADGR_RESPONSE = {
    "id": "https://DOMAIN/assertions/42",
    "name": "Teamwork Badge",
    "issued_on": "2024-06-15T10:00:00Z",
    "badgeclass": {
        "id": "https://DOMAIN/badges/18",
        "name": "Teamwork Badge",
        "description": "Demonstrates teamwork ability",
        "criteria_text": "Complete the project",
        "issuer": {
            "id": "https://DOMAIN/issuers/1",
            "name_dutch": "Test NL",
            "name_english": "Test Corp",
        },
    },
    "given_name": "Jan",
    "family_name": "Jansen",
}

_BADGR_RESPONSE_WITH_IMAGE = {
    "id": "https://DOMAIN/assertions/43",
    "name": "Coding Badge",
    "issued_on": "2024-06-15T11:00:00Z",
    "badgeclass": {
        "id": "https://DOMAIN/badges/19",
        "name": "Coding Badge",
        "description": "Demonstrates coding skills",
        "criteria_text": "Write a program",
        "image": "https://DOMAIN/images/coding-badge.png",
        "issuer": {
            "id": "https://DOMAIN/issuers/1",
            "name_dutch": "Test NL",
            "name_english": "Test Corp",
        },
    },
    "given_name": "Anna",
    "family_name": "de Vries",
}

class TestResolveCredentialId:
    """Tests for the _resolve_credential_id helper."""

    def test_returns_id_when_present(self):
        """_resolve_credential_id returns dto.entity_id when set."""
        dto = _BadgrAwardResponse.from_dict(_VALID_BADGR_RESPONSE)
        assert _resolve_credential_id(dto) == "https://DOMAIN/assertions/42"

    def test_raises_when_id_missing(self):
        """_resolve_credential_id raises AwardMappingError when entity_id is None."""
        dto = _BadgrAwardResponse.from_dict({})
        with pytest.raises(AwardMappingError, match="missing 'id'"):
            _ = _resolve_credential_id(dto)


class TestResolveBadgeName:
    """Tests for the _resolve_badge_name helper."""

    def test_returns_dto_name_when_present(self):
        """_resolve_badge_name returns dto.name when set."""
        dto = _BadgrAwardResponse.from_dict(_VALID_BADGR_RESPONSE)
        assert _resolve_badge_name(dto) == "Teamwork Badge"

    def test_fallback_to_badgeclass_name(self):
        """_resolve_badge_name falls back to badgeclass.name when dto.name is None."""
        dto = _BadgrAwardResponse.from_dict(
            {"name": None, "badgeclass": {"name": "Badge B"}}
        )
        assert _resolve_badge_name(dto) == "Badge B"

    def test_returns_empty_string_when_no_name_anywhere(self):
        """_resolve_badge_name returns '' when no name source is present."""
        dto = _BadgrAwardResponse.from_dict({"name": None, "badgeclass": None})
        assert _resolve_badge_name(dto) == ""


class TestResolveValidFrom:
    """Tests for the _resolve_valid_from helper."""

    def test_returns_issued_on_when_present(self):
        """_resolve_valid_from returns dto.issued_on when set."""
        dto = _BadgrAwardResponse.from_dict(_VALID_BADGR_RESPONSE)
        assert _resolve_valid_from(dto) == "2024-06-15T10:00:00Z"

    def test_returns_empty_string_when_issued_on_missing(self):
        """_resolve_valid_from returns '' when dto.issued_on is None."""
        dto = _BadgrAwardResponse.from_dict({"issued_on": None})
        assert _resolve_valid_from(dto) == ""


class TestOb3AwardFromBadgrApi:
    """Tests for ob3_award_from_badgr_api_response."""

    def test_produces_valid_ob3_award(self):
        """Full response produces an OB3Award with all fields populated."""
        award = ob3_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert isinstance(award, OB3Award)
        assert award.id == "https://DOMAIN/assertions/42"
        assert award.name == "Teamwork Badge"
        assert award.validFrom == "2024-06-15T10:00:00Z"
        assert award.credentialSubject.achievement.name == "Teamwork Badge"
        assert award.credentialSubject.achievement.description == (
            "Demonstrates teamwork ability"
        )

    def test_missing_id_raises_mapping_error(self):
        """A response without ``id`` raises instead of producing an empty id."""
        with pytest.raises(AwardMappingError, match="missing 'id'"):
            _ = ob3_award_from_badgr_api_response({})

    def test_produces_image_when_image_present(self):
        """Full response with image produces an OB3Award with achievement.image."""
        award = ob3_award_from_badgr_api_response(_BADGR_RESPONSE_WITH_IMAGE)
        assert award.credentialSubject.achievement.image is not None
        assert award.credentialSubject.achievement.image["id"] == (
            "https://DOMAIN/images/coding-badge.png"
        )
        assert award.credentialSubject.achievement.image["type"] == "Image"

    def test_achievement_image_is_none_when_no_image(self):
        """Full response without image produces None for achievement.image."""
        award = ob3_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert award.credentialSubject.achievement.image is None

    def test_uses_badgeclass_image(self):
        """_resolve_image uses badgeclass.image when present."""
        award = ob3_award_from_badgr_api_response(
            {
                "id": "https://DOMAIN/assertions/44",
                "name": "Double Image",
                "issued_on": "2024-06-15T12:00:00Z",
                "badgeclass": {
                    "id": "https://DOMAIN/badges/20",
                    "name": "Double Image",
                    "description": "Has an image",
                    "criteria_text": "Do stuff",
                    "image": "https://DOMAIN/badges/20/image",
                    "issuer": {
                        "id": "https://DOMAIN/issuers/1",
                        "name_dutch": "Test NL",
                        "name_english": "Test Corp",
                    },
                },
            }
        )
        assert award.credentialSubject.achievement.image is not None
        assert award.credentialSubject.achievement.image["id"] == (
            "https://DOMAIN/badges/20/image"
        )


