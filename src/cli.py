"""Command-line adapter for sysadmin operations."""

import sys

from src.config.config import EnvConfigRepo
from src.credential_configurations import (
    ssi_agent_credential_configurations_client_adapter as ssi_adapter,
)
from src.credential_configurations.credential_configurations_service import (
    CredentialConfigurationsService,
)
from src.credential_configurations.credential_configurations_cli_adapter import (
    CredentialConfigurationsCliAdapter,
)

_USAGE = """\
Usage: ec-issuer <command> [args]

Commands:
    credential-configuration  - Manage credential configurations
"""


def main() -> None:
    """Entry point for the ec-issuer command."""
    config = EnvConfigRepo()

    # Initialize credential configurations client and service
    client = ssi_adapter.SsiAgentCredentialConfigurationsClientAdapter(
        ssi_agent_url=config.ssi_agent_url
    )
    service = CredentialConfigurationsService(client=client)
    cli_adapter = CredentialConfigurationsCliAdapter(service=service)

    match sys.argv[1:]:
        case ["credential-configuration", *args]:
            cli_adapter.handle_command(args)
        case _:
            print(_USAGE, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
