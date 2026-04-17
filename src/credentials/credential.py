"""Credential domain models."""

from dataclasses import dataclass


@dataclass
class Credential:
    """Domain model representing a single credential."""

    credential: str


@dataclass
class CredentialResponse:
    """Domain model representing a credential response."""

    credentials: list[Credential]
