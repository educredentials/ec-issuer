"""CLI adapter for sysadmin operations."""

import sys
from dataclasses import asdict, dataclass
from typing import override

import msgspec

from src.credential_configurations.credential_configurations_service import (
    CredentialConfigurationsService,
)
from src.credential_configurations.models import CredentialConfiguration, Display

from .sysadmin_port import SysadminPort

USAGE = """\
Usage: ec-issuer <command> [args]

Commands:
    credential-configuration  - Manage credential configurations
"""

CREDENTIAL_CONFIG_USAGE = """\
Usage: ec-issuer credential-configuration <command> [args]

Commands:
    create    - Create a new config (reads JSON from stdin)
    show <id> - Show a credential configuration by ID
    list      - List all credential configurations
    update <id> - Update a config (reads JSON from stdin)
"""


@dataclass
class _CredentialConfigurationInput:
    """Input structure for credential configuration from CLI."""

    format: str
    credential_configuration_id: str | None = None
    display: list[Display] | None = None
    credential_definition: dict[str, object] | None = None
    cryptographic_binding_methods_supported: list[str] | None = None
    credential_signing_alg_values_supported: list[str] | None = None
    proof_types_supported: dict[str, object] | None = None


class SysadminCliAdapter(SysadminPort):
    """CLI adapter for sysadmin operations."""

    _credential_configurations_service: CredentialConfigurationsService

    def __init__(
        self, credential_configurations_service: CredentialConfigurationsService
    ) -> None:
        """Initialize the adapter.

        Args:
            service: The credential configurations service.
        """
        self._credential_configurations_service = credential_configurations_service

    @override
    def run(self, command: list[str]) -> None:
        """Run a sysadmin command.

        Args:
            command: The command and its arguments.
        """
        match command:
            case []:
                print(USAGE, file=sys.stderr)
                sys.exit(1)
            case ["credential-configuration"]:
                print(CREDENTIAL_CONFIG_USAGE, file=sys.stderr)
                sys.exit(1)
            case ["credential-configuration", "create"]:
                self._handle_create()
            case ["credential-configuration", "show", config_id]:
                self._handle_show(config_id)
            case ["credential-configuration", "list"]:
                self._handle_list()
            case ["credential-configuration", "update", config_id]:
                self._handle_update(config_id)
            case ["credential-configuration", *_]:
                print(CREDENTIAL_CONFIG_USAGE, file=sys.stderr)
                sys.exit(1)
            case _:
                print(USAGE, file=sys.stderr)
                sys.exit(1)

    def _handle_create(self) -> None:
        """Handle the create command."""
        try:
            input_json = sys.stdin.read()
            config_data: _CredentialConfigurationInput = msgspec.json.decode(
                input_json, type=_CredentialConfigurationInput
            )

            configuration = CredentialConfiguration(
                credential_configuration_id=config_data.credential_configuration_id,
                format=config_data.format,
                display=config_data.display,
                credential_definition=config_data.credential_definition,
                cryptographic_binding_methods_supported=config_data.cryptographic_binding_methods_supported,
                credential_signing_alg_values_supported=config_data.credential_signing_alg_values_supported,
                proof_types_supported=config_data.proof_types_supported,
            )

            result = self._credential_configurations_service.create(configuration)
            print(msgspec.json.encode(asdict(result)).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_show(self, config_id: str) -> None:
        """Handle the show command."""
        try:
            result = self._credential_configurations_service.get(config_id)
            print(msgspec.json.encode(asdict(result)).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_list(self) -> None:
        """Handle the list command."""
        try:
            results = self._credential_configurations_service.list()
            # Convert to list of dicts for JSON serialization
            results_list = [asdict(r) for r in results]
            print(msgspec.json.encode(results_list).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_update(self, config_id: str) -> None:
        """Handle the update command."""
        try:
            input_json = sys.stdin.read()
            config_data: _CredentialConfigurationInput = msgspec.json.decode(
                input_json, type=_CredentialConfigurationInput
            )

            # Ensure the ID from the command matches the ID in the JSON
            config_data.credential_configuration_id = config_id

            configuration = CredentialConfiguration(
                credential_configuration_id=config_data.credential_configuration_id,
                format=config_data.format,
                display=config_data.display,
                credential_definition=config_data.credential_definition,
                cryptographic_binding_methods_supported=config_data.cryptographic_binding_methods_supported,
                credential_signing_alg_values_supported=config_data.credential_signing_alg_values_supported,
                proof_types_supported=config_data.proof_types_supported,
            )

            result = self._credential_configurations_service.update(configuration)
            print(msgspec.json.encode(asdict(result)).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
