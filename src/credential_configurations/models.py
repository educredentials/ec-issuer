"""Models for credential configurations."""

from dataclasses import dataclass


@dataclass
class Display:
    """Display information for a credential configuration."""

    locale: str
    name: str
    logo: dict[str, str | None] | None = None


@dataclass
class CredentialDefinition:
    type: list[str]
    format: str | None = None


@dataclass
class CredentialMetadata:
    display: list[Display] | None = None


@dataclass
class ProofTypesSupportedJwt:
    jwt: dict[str, list[str]]

@dataclass
class CredentialConfiguration:
    """Represents a credential configuration."""

    format: str
    credential_metadata: CredentialMetadata
    proof_types_supported: ProofTypesSupportedJwt

    credential_configuration_id: str = ""

    credential_definition: CredentialDefinition | None = None
    credential_signing_alg_values_supported: list[str] | None = None
    cryptographic_binding_methods_supported: list[str] | None = None
