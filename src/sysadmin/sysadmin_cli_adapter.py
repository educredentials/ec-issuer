"""CLI adapter for sysadmin operations."""

import sys
from dataclasses import asdict
from typing import override

import msgspec

from src.credential_configurations.credential_configurations_service import (
    CredentialConfigurationsService,
)
from src.credential_configurations.models import (
    CredentialConfiguration,
)

from .sysadmin_port import SysadminPort

USAGE = """\
Usage: ec-issuer <command> [args]

Commands:
    credential-configuration  - Manage credential configurations
"""

CREDENTIAL_CONFIG_USAGE = """\
Usage: ec-issuer credential-configuration <command> [args]

Commands:
    create <id> - Create a new config (reads JSON from stdin)
    show <id>   - Show a credential configuration by ID
    update <id> - Update a config (reads JSON from stdin)
    list        - List all credential configurations
"""


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
            case ["credential-configuration", "create", config_id]:
                self._handle_create(config_id)
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

    def _handle_create(self, config_id: str) -> None:
        """Handle the create command."""
        try:
            input_json = sys.stdin.read()
            configuration: CredentialConfiguration = msgspec.json.decode(
                input_json, type=CredentialConfiguration
            )
            configuration.credential_configuration_id = config_id
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
        self._handle_create(config_id)
