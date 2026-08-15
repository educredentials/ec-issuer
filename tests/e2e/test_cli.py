"""End-to-end tests for credential-configuration CLI commands."""

from dataclasses import dataclass
import os
from subprocess import PIPE, Popen

import msgspec
import pytest


@dataclass
class _Logo:
    """Logo display information."""

    uri: str
    alt_text: str


@dataclass
class _Display:
    """
    Display information for a credential configuration. Used in output

    Intentionally duplicated from src.credential_configurations to decouple tests
    from implementation
    """

    name: str
    logo: _Logo | None = None
    locale: str | None = None
    description: str | None = None


@dataclass
class _CredentialTemplate:
    """Output structure from CLI credential configuration commands.

    Matches the actual CredentialTemplate dataclass used by the CLI.
    """

    type: list[str]
    id: str = ""
    title: str | None = None
    display: _Display | None = None
    dataModel: str | None = None
    creator: str | None = None
    holderType: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    visibility: str | None = None
    description: str | None = None
    schema: dict[str, object] | None = None
    credentialExpiration: dict[str, str] | None = None


def process(subcommand: str, args: list[str] | None = None) -> Popen[str]:
    command = ["uv", "run", "ec-issuer-cli", "credential-configuration", subcommand]
    if args:
        command.extend(args)

    env = os.environ.copy()

    return Popen(
        command,
        stdin=PIPE,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
        env=env,
    )


def _assert_credential_config_create(
    create_output: _CredentialTemplate,
) -> None:
    """Common assertions for create/show output."""
    assert create_output.id == "OpenbadgeCredential"

    assert create_output.display is not None
    assert create_output.display.name == "Open Badge Credential"

    assert create_output.type == [
        "VerifiableCredential",
        "OpenBadgeCredential",
    ]


@pytest.mark.e2e
class TestCredentialTemplateCli:
    """Test the credential-configuration CLI commands."""

    def test_create_credential_configuration(
        self, credential_configuration_input: str
    ) -> None:
        """Test that create returns the created configuration."""
        create_process = process("create", ["OpenbadgeCredential"])
        stdout, stderr = create_process.communicate(
            input=credential_configuration_input
        )

        assert create_process.returncode == 0, f"Create failed: {stderr}"
        create_output = msgspec.json.decode(stdout, type=_CredentialTemplate)

        _assert_credential_config_create(create_output)

    def test_list_credential_configurations(self) -> None:
        """Test that list returns configurations."""
        list_process = process("list")
        stdout, stderr = list_process.communicate()

        assert list_process.returncode == 0, f"List failed: {stderr}"
        list_output: list[_CredentialTemplate] = msgspec.json.decode(
            stdout, type=list[_CredentialTemplate]
        )
        assert isinstance(list_output, list)
        # Should contain the configuration returned by mock
        assert any(
            config.id == "OpenbadgeCredential"
            for config in list_output
        )

    def test_show_credential_configuration(self) -> None:
        """Test that show returns a configuration."""
        show_process = process("show", ["OpenbadgeCredential"])
        stdout, stderr = show_process.communicate()

        assert show_process.returncode == 0, f"Show failed: {stderr}"
        show_output = msgspec.json.decode(stdout, type=_CredentialTemplate)

        _assert_credential_config_create(show_output)

    def test_update_credential_configuration(
        self, credential_configuration_input: str
    ) -> None:
        """Test that update updates a configuration."""
        # First create a configuration
        create_process = process("create", ["OpenbadgeCredential"])
        _, stderr = create_process.communicate(input=credential_configuration_input)
        assert create_process.returncode == 0, f"Create failed: {stderr}"

        # Update the same input (mock returns static response)
        update_process = process("update", ["OpenbadgeCredential"])
        stdout, stderr = update_process.communicate(
            input=credential_configuration_input
        )

        assert update_process.returncode == 0, f"Update failed: {stderr}"
        update_output = msgspec.json.decode(stdout, type=_CredentialTemplate)
        assert update_output.id == "OpenbadgeCredential"

    def test_invalid_command(self) -> None:
        """Test that invalid commands return an error."""
        invalid_process = process("invalid")
        _, stderr = invalid_process.communicate()

        assert invalid_process.returncode == 1
        assert "Usage:" in stderr

    def test_show_nonexistent(self) -> None:
        """Test that showing a non-existent configuration returns an error."""
        nonexistent_process = process("show", ["nonexistent"])
        _, stderr = nonexistent_process.communicate()

        assert nonexistent_process.returncode == 1
        assert "Error:" in stderr

    def test_delete_credential_configuration(
        self, credential_configuration_input: str
    ) -> None:
        """Test that delete removes a credential configuration."""
        create_process = process("create", ["OpenbadgeCredential"])
        stdout, stderr = create_process.communicate(
            input=credential_configuration_input
        )
        assert create_process.returncode == 0, f"Create failed: {stderr}"

        show_process = process("show", ["OpenbadgeCredential"])
        stdout, _ = show_process.communicate()
        assert show_process.returncode == 0

        delete_process = process("delete", ["OpenbadgeCredential"])
        stdout, stderr = delete_process.communicate()
        assert delete_process.returncode == 0, f"Delete failed: {stderr}"
        assert "deleted" in stdout.lower()

    def test_delete_nonexistent_returns_success(self) -> None:
        """Test that delete succeeds against the mock (always returns 204)."""
        delete_process = process("delete", ["nonexistent-template-id"])
        stdout, _ = delete_process.communicate()

        assert delete_process.returncode == 0
        assert "deleted" in stdout.lower()
