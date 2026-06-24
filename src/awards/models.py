"""
Domain models for awards (OB3 AchievementCredential).

Currently a pragmatic, simple version of a full OpenbadgeCredential.

The full OpenBadgeCredential, with all possible fields, and nested
objects, is described in https://www.imsglobal.org/spec/ob/v3p0/#org-1edtech-ob-v3p0-model-0
Starting at AchiementCredential, which is our Award.
"""

from dataclasses import dataclass


@dataclass
class Criteria:
    """Criteria for earning an achievement."""

    narrative: str


@dataclass
class Achievement:
    """An achievement within an award."""

    id: str
    type: list[str]
    criteria: Criteria
    description: str
    name: str


@dataclass
class AchievementSubject:
    """The subject of an AchievementCredential."""

    id: str
    type: list[str]
    achievement: Achievement


@dataclass
class Issuer:
    """The issuer of an AchievementCredential."""

    id: str
    type: list[str]
    name: str


@dataclass
class Award:
    """Minimal OB3 AchievementCredential (unsigned)."""

    id: str
    type: list[str]
    name: str
    issuer: Issuer
    validFrom: str
    credentialSubject: AchievementSubject
