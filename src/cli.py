#!/usr/bin/env python3
"""Command-line application entry point for the EC Issuer."""

from src.config.config import EnvConfigRepo
from src.credential_configurations import (
    ssi_agent_credential_configurations_client_adapter as ssi_adapter,
)
from src.sysadmin.sysadmin_cli_adapter import SysadminCliAdapter


class App:
    """Command-line application entry point."""

    _sysadmin_port: SysadminCliAdapter

    def __init__(self) -> None:
        """Initialise and wire all application dependencies."""
        config = EnvConfigRepo()

        client = ssi_adapter.SsiAgentCredentialTemplateClientAdapter(
            ssi_agent_url=config.ssi_agent_url
        )

        self._sysadmin_port = SysadminCliAdapter(client=client)

    def run(self, args: list[str]) -> None:
        """Run the application.

        Args:
            args: Command line arguments.
        """
        self._sysadmin_port.run(args)


def main() -> None:
    """Entry point for the ec-issuer command."""
    import sys

    app = App()
    app.run(sys.argv[1:])


if __name__ == "__main__":
    main()
