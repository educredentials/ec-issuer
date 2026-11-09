"""Unit tests for award conversion functions (models module).

Tests the data flow from raw Badgr API JSON through DTOs to OB3Award
domain models. Covers edge cases: missing fields, None badgeclass, fallback
chains -- all tested through the public interface only.
"""

import pytest

from src.awards.badgr_mapping import (
    AwardMappingError,
    ob3_award_from_badgr_api_response,
)
from src.awards.models import OB3Award

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
    """Edge-case tests for credential ID resolution via public interface."""

    def test_returns_id_when_present(self):
        """Valid response produces an OB3Award with the correct credential id."""
        award = ob3_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert award.id == "https://DOMAIN/assertions/42"


class TestResolveBadgeName:
    """Badge name resolution tested via public interface."""

    def test_returns_dto_name_when_present(self):
        """award.name uses dto.name when set."""
        award = ob3_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert award.name == "Teamwork Badge"

    def test_fallback_to_badgeclass_name(self):
        """award.name falls back to badgeclass.name when dto.name is None."""
        award = ob3_award_from_badgr_api_response(
            {
                "id": "https://DOMAIN/assertions/99",
                "name": None,
                "badgeclass": {
                    "id": "https://DOMAIN/badges/1",
                    "name": "Badge B",
                    "issuer": {"id": "https://DOMAIN/issuers/1", "name": "Test"},
                },
            }
        )
        assert award.name == "Badge B"

    def test_empty_when_both_names_missing(self):
        """award.name is '' when dto.name is None and badgeclass is None."""
        award = ob3_award_from_badgr_api_response(
            {"id": "https://DOMAIN/assertions/99", "name": None, "badgeclass": None}
        )
        assert award.name == ""


class TestResolveValidFrom:
    """validFrom resolution tested via public interface."""

    def test_returns_issued_on_when_present(self):
        """award.validFrom uses dto.issued_on when set."""
        award = ob3_award_from_badgr_api_response(_VALID_BADGR_RESPONSE)
        assert award.validFrom == "2024-06-15T10:00:00Z"

    def test_returns_empty_string_when_issued_on_missing(self):
        """award.validFrom is '' when dto.issued_on is None."""
        award = ob3_award_from_badgr_api_response(
            {
                "id": "https://DOMAIN/assertions/99",
                "issued_on": None,
                "badgeclass": {
                    "id": "https://DOMAIN/badges/1",
                    "name": "Badge",
                    "description": "Test",
                    "criteria_text": "Do stuff",
                    "issuer": {"id": "https://DOMAIN/issuers/1", "name": "Test"},
                },
            }
        )
        assert award.validFrom == ""


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
        """award uses badgeclass.image when present."""
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
