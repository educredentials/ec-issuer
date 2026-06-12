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
class _CredentialConfiguration:
    """Output structure from CLI credential configuration commands.

    Intentially decoupled from src.credential_configurations to decouple tests
    from implementation
    """

    format: str
    credential_definition: dict[str, object] | None = None
    credential_configuration_id: str | None = None
    credential_metadata: dict[str, list[_Display] | None] | None = None
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

    def test_create_credential_configuration(self, credential_configuration_input: str):
        """Test that create returns the created configuration."""
        create_process = process("create", ["OpenbadgeCredential"])
        stdout, stderr = create_process.communicate(
            input=credential_configuration_input
        )

        assert create_process.returncode == 0, f"Create failed: {stderr}"
        create_output = msgspec.json.decode(stdout, type=_CredentialConfiguration)
        assert create_output.credential_configuration_id == "OpenbadgeCredential"

        assert create_output.credential_metadata is not None
        assert create_output.credential_metadata["display"] is not None
        assert len(create_output.credential_metadata["display"]) == 2
        assert (
            create_output.credential_metadata["display"][0].name
            == "Open Badge Credential"
        )
        assert create_output.credential_definition is not None
        assert create_output.credential_definition["type"] == [
            "VerifiableCredential",
            "OpenbadgeCredential",
        ]

    def test_list_credential_configurations(self):
        """Test that list returns configurations."""
        list_process = process("list")
        stdout, stderr = list_process.communicate()

        assert list_process.returncode == 0, f"List failed: {stderr}"
        list_output: list[_CredentialConfiguration] = msgspec.json.decode(
            stdout, type=list[_CredentialConfiguration]
        )
        assert isinstance(list_output, list)
        # Should contain the configuration assigned in mock
        assert any(
            config.credential_configuration_id == "OpenbadgeCredential"
            for config in list_output
        )

    def test_show_credential_configuration(self):
        """Test that show returns a configuration."""
        show_process = process("show", ["OpenbadgeCredential"])
        stdout, stderr = show_process.communicate()

        assert show_process.returncode == 0, f"Show failed: {stderr}"
        show_output = msgspec.json.decode(stdout, type=_CredentialConfiguration)
        assert show_output.credential_configuration_id == "OpenbadgeCredential"
        assert show_output.format == "vc+sd-jwt"

    def test_update_credential_configuration(self, credential_configuration_input: str):
        """Test that update updates a configuration."""
        # First create a configuration
        create_process = process("create", ["OpenbadgeCredential"])
        _, stderr = create_process.communicate(input=credential_configuration_input)
        assert create_process.returncode == 0, f"Create failed: {stderr}"

        # Now update the configuration, for that, create a mutable object from fixture
        update_input = msgspec.json.decode(
            credential_configuration_input, type=_CredentialConfiguration
        )

        # Remove a type to test we can remove items from arrays
        # Update name to test we can update items
        assert update_input.credential_definition is not None
        update_input.credential_definition["type"] = ["VerifiableCredential"]
        update_input.credential_metadata = {
            "display": [_Display(name="Updated Name", locale="en")]
        }
        json_str = msgspec.json.encode(update_input).decode()

        update_process = process("update", ["OpenbadgeCredential"])
        stdout, stderr = update_process.communicate(input=json_str)

        assert update_process.returncode == 0, f"Update failed: {stderr}"
        update_output = msgspec.json.decode(stdout, type=_CredentialConfiguration)
        assert update_output.credential_configuration_id == "OpenbadgeCredential"

        # Our mock server cannot handle dynamic resources, it always returns
        # a fixed json for credential issuer metadata.
        # So we cannot test that an update request actually updates the resources
        # on the service.
        # Using the "real-ssi-server" will show the items being updated, but this
        # service has state, so re-running tests will result in failures due to
        # accumulating state - e.g. the update will change the name, but then
        # following list/get will get that name instead of the one they assert
        # against

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
