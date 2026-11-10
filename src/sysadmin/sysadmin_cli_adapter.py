"""CLI adapter for sysadmin operations."""

import sys
from dataclasses import asdict
from typing import override

import msgspec

from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateClientPort,
)
from src.revocation.revocation_client_port import RevocationClientPort
from src.credential_configurations.models import (
    CredentialTemplate,
)

from .sysadmin_port import SysadminPort

USAGE = """\
Usage: ec-issuer <command> [args]

Commands:
    credential-configuration  - Manage credential configurations
    revoke <id>               - Revoke an issued credential by ID
"""

CREDENTIAL_CONFIG_USAGE = """\
Usage: ec-issuer credential-configuration <command> [args]

Commands:
    create <id> - Create a new config (reads JSON from stdin)
    show <id>   - Show a credential configuration by ID
    update <id> - Update a config (reads JSON from stdin)
    delete <id> - Delete a credential configuration by ID
    list        - List all credential configurations
"""


class SysadminCliAdapter(SysadminPort):
    """CLI adapter for sysadmin operations."""

    _client: CredentialTemplateClientPort
    _revocation_client: RevocationClientPort

    def __init__(
        self,
        client: CredentialTemplateClientPort,
        revocation_client: RevocationClientPort,
    ) -> None:
        """Initialize the adapter.

        Args:
            client: A CredentialTemplateClientPort implementation.
            revocation_client: A RevocationClientPort implementation.
        """
        self._client = client
        self._revocation_client = revocation_client

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
            case ["credential-configuration", "delete", config_id]:
                self._handle_delete(config_id)
            case ["credential-configuration", "list"]:
                self._handle_list()
            case ["credential-configuration", "update", config_id]:
                self._handle_update(config_id)
            case ["credential-configuration", *_]:
                print(CREDENTIAL_CONFIG_USAGE, file=sys.stderr)
                sys.exit(1)
            case ["revoke", credential_id]:
                self._handle_revoke(credential_id)
            case ["revoke", *_]:
                print(USAGE, file=sys.stderr)
                sys.exit(1)
            case _:
                print(USAGE, file=sys.stderr)
                sys.exit(1)

    def _handle_create(self, _config_id: str) -> None:
        """Handle the create command."""
        try:
            input_json = sys.stdin.read()
            configuration: CredentialTemplate = msgspec.json.decode(
                input_json, type=CredentialTemplate
            )
            result = self._client.create(configuration)
            configuration.id = result.id
            print(msgspec.json.encode(asdict(result)).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_show(self, config_id: str) -> None:
        """Handle the show command."""
        try:
            result = self._client.get(config_id)
            print(msgspec.json.encode(asdict(result)).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_list(self) -> None:
        """Handle the list command."""
        try:
            results = self._client.list()
            # Convert to list of dicts for JSON serialization
            results_list = [asdict(r) for r in results]
            print(msgspec.json.encode(results_list).decode())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_update(self, config_id: str) -> None:
        """Handle the update command."""
        self._handle_create(config_id)

    def _handle_delete(self, config_id: str) -> None:
        """Handle the delete command."""
        try:
            self._client.delete(config_id)
            print(f'Configuration "{config_id}" deleted')
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _handle_revoke(self, credential_id: str) -> None:
        """Handle the revoke command."""
        try:
            self._revocation_client.revoke(credential_id)
            print(f'Credential "{credential_id}" revoked')
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
