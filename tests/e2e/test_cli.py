"""End-to-end tests for credential-configuration CLI commands."""

from dataclasses import dataclass
from subprocess import PIPE, Popen

import msgspec
import pytest


@dataclass
class _Display:
    """
    Display information for a credential configuration. Used in input and output

    Intentially duplicated from src.credential_configurations to decouple tests
    from implementation
    """

    locale: str
    name: str
    logo: dict[str, str | None] | None = None


@dataclass
class CredentialConfigurationOutput:
    """Output structure from CLI credential configuration commands."""

    credential_configuration_id: str
    format: str
    display: list[_Display] | None = None
    credential_definition: dict[str, object] | None = None
    cryptographic_binding_methods_supported: list[str] | None = None
    credential_signing_alg_values_supported: list[str] | None = None
    proof_types_supported: dict[str, object] | None = None


@dataclass
class CredentialConfigurationInput:
    """
    Input structure for credential configuration from CLI.

    Intentially duplicated from src.credential_configurations to decouple tests
    from implementation
    """

    credential_configuration_id: str
    format: str
    display: list[_Display] | None = None
    credential_definition: dict[str, object] | None = None
    cryptographic_binding_methods_supported: list[str] | None = None
    credential_signing_alg_values_supported: list[str] | None = None
    proof_types_supported: dict[str, object] | None = None


def process(subcommand: str, args: None | list[str] = None) -> Popen[str]:
    command = ["uv", "run", "ec-issuer-cli", "credential-configuration", subcommand]
    if args:
        command.extend(args)

    process = Popen(
        command,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )
    return process


@pytest.mark.e2e
class TestCredentialConfigurationCli:
    """Test the credential-configuration CLI commands."""

    def test_create_credential_configuration_minimal(
        self, credential_configuration_minimal: str
    ):
        """Test that create returns the created configuration."""
        create_process = process("create")
        stdout, stderr = create_process.communicate(
            input=credential_configuration_minimal
        )

        assert create_process.returncode == 0, f"Create failed: {stderr}"
        create_output = msgspec.json.decode(stdout, type=CredentialConfigurationOutput)
        assert create_output

    def test_create_credential_configuration_full(
        self, credential_configuration_full: str
    ):
        """Test that create returns the created configuration."""
        create_process = process("create")
        stdout, stderr = create_process.communicate(input=credential_configuration_full)

        assert create_process.returncode == 0, f"Create failed: {stderr}"
        create_output = msgspec.json.decode(stdout, type=CredentialConfigurationOutput)
        assert create_output

    def test_list_credential_configurations(self):
        """Test that list returns configurations."""
        list_process = process("list")
        stdout, stderr = list_process.communicate()

        assert list_process.returncode == 0, f"List failed: {stderr}"
        list_output: list[CredentialConfigurationOutput] = msgspec.json.decode(
            stdout, type=list[CredentialConfigurationOutput]
        )
        assert isinstance(list_output, list)
        # Should contain the configuration assigned in mock
        assert any(
            config.credential_configuration_id == "OpenBadgeCredential"
            for config in list_output
        )

    def test_show_credential_configuration(self):
        """Test that show returns a configuration."""
        show_process = process("show", ["OpenBadgeCredential"])
        stdout, stderr = show_process.communicate()

        assert show_process.returncode == 0, f"Show failed: {stderr}"
        show_output = msgspec.json.decode(stdout, type=CredentialConfigurationOutput)
        assert show_output.credential_configuration_id == "OpenBadgeCredential"
        assert show_output.format == "jwt_vc_json"

    def test_update_credential_configuration(self, credential_configuration_full: str):
        """Test that update updates a configuration."""
        # First create a configuration
        create_process = process("create")
        stdout, stderr = create_process.communicate(input=credential_configuration_full)

        assert create_process.returncode == 0, f"Create failed: {stderr}"

        # Now update the configuration
        update_input = msgspec.json.decode(
            credential_configuration_full, type=CredentialConfigurationInput
        )

        # Test that we can remove items from arrays
        assert update_input.credential_definition is not None
        update_input.credential_definition["type"] = ["VerifiableCredential"]

        # Test that we can change a display name
        assert update_input.display is not None
        update_input.display[0].name = "Updated Name"

        json_str = msgspec.json.encode(update_input).decode()

        update_process = process("update", ["test_config_3"])
        stdout, stderr = update_process.communicate(input=json_str)

        assert update_process.returncode == 0, f"Update failed: {stderr}"
        update_output = msgspec.json.decode(stdout, type=CredentialConfigurationOutput)
        assert update_output.credential_configuration_id == "test_config_3"

        assert update_output.credential_definition is not None
        # Test that we can remove items from arrays
        assert update_output.credential_definition["type"] == ["VerifiableCredential"]
        assert update_output.display is not None
        # Test that we can change a display name
        assert update_output.display[0].name == "Updated Name"

    def test_invalid_command(self):
        """Test that invalid commands return an error."""
        invalid_process = process("invalid")
        _, stderr = invalid_process.communicate()

        assert invalid_process.returncode == 1
        assert "Usage:" in stderr

    def test_show_nonexistent(self):
        """Test that showing a non-existent configuration returns an error."""
        nonexistent_process = process("show", ["nonexistent"])
        _, stderr = nonexistent_process.communicate()

        assert nonexistent_process.returncode == 1
        assert "Error:" in stderr
