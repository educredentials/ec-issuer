"""Models for credential configurations."""

from dataclasses import dataclass, field


@dataclass
class Logo:
    """Logo display information."""

    uri: str
    alt_text: str


@dataclass
class Display:
    """Display information for a credential configuration."""

    name: str
    logo: Logo | None = None


@dataclass
class CredentialDefinition:
    type: list[str]
    format: str | None = None


@dataclass
class CredentialMetadata:
    display: list[Display] | None = None


@dataclass
class CredentialTemplate:
    """Represents a credential template.

    Supports both the OpenID4VCI credential issuer metadata format
    and the custom OBv3-specific metadata (dataModel, holderType, etc.).
    """

    type: list[str]
    id: str = ""
    title: str | None = None
    display: Display | None = None
    dataModel: str | None = None
    creator: str | None = None
    holderType: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    visibility: str | None = None
    description: str | None = None
    schema: dict[str, object] = field(default_factory=dict)
