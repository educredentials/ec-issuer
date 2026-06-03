"""Models for credential configurations."""

from dataclasses import dataclass


@dataclass
class Display:
    """Display information for a credential configuration."""

    locale: str
    name: str
    logo: dict[str, str | None] | None = None


@dataclass
class CredentialConfiguration:
    """Represents a credential configuration."""

    format: str
    credential_configuration_id: str | None = None
    display: list[Display] | None = None
    credential_definition: dict[str, object] | None = None
    cryptographic_binding_methods_supported: list[str] | None = None
    credential_signing_alg_values_supported: list[str] | None = None
    proof_types_supported: dict[str, object] | None = None
