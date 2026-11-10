from unittest.mock import MagicMock, patch
from typing import cast
from io import StringIO
import sys

from src.cli import App
from src.sysadmin.sysadmin_cli_adapter import SysadminCliAdapter
from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateClientPort,
)
from src.revocation.revocation_client_port import RevocationClientPort


class TestCliApp:
    """Tests for the CLI App entry point."""

    def test_main_calls_sysadmin_run(self) -> None:
        """main() instantiates App and calls run with sys.argv[1:]."""
        mock_config_instance = MagicMock()
        mock_config_instance.ssi_agent_url = "http://test:8000"
        mock_sysadmin = cast(SysadminCliAdapter, MagicMock())
        with (
            patch(
                "src.cli.EnvConfigRepo", return_value=mock_config_instance
            ),
            patch(
                "src.cli.ssi_adapter.SsiAgentCredentialTemplateClientAdapter"
            ),
            patch(
                "src.cli.SysadminCliAdapter", return_value=mock_sysadmin
            ),
        ):
            _ = App()
            mock_sysadmin.run(["bootstrap"])


class TestSysadminCliAdapterRevoke:
    """Tests for the revoke command in SysadminCliAdapter."""

    def test_revoke_calls_revocation_client(
        self,
    ) -> None:
        """revoke command invokes revocation_client.revoke with the credential ID."""
        mock_config = MagicMock()
        mock_config.ssi_agent_url = "http://agent:8000"
        mock_config_template_client = MagicMock(spec=CredentialTemplateClientPort)
        mock_revocation_client = MagicMock(spec=RevocationClientPort)

        from src.cli import App

        with (
            patch(
                "src.cli.EnvConfigRepo", return_value=mock_config
            ),
            patch(
                "src.cli.ssi_adapter.SsiAgentCredentialTemplateClientAdapter",
                return_value=mock_config_template_client,
            ),
            patch(
                "src.cli.SsiAgentRevocationClientAdapter",
                return_value=mock_revocation_client,
            ),
        ):
            app = App()
            app.run(["revoke", "cred-abc-123"])

        mock_revocation_client.revoke.assert_called_once_with("cred-abc-123")

    def test_revoke_prints_success_message(
        self,
    ) -> None:
        """revoke prints success message to stdout."""
        from src.sysadmin.sysadmin_cli_adapter import SysadminCliAdapter

        mock_config = MagicMock()
        mock_config.ssi_agent_url = "http://agent:8000"
        mock_config_template_client = MagicMock(spec=CredentialTemplateClientPort)
        mock_revocation_client = MagicMock(spec=RevocationClientPort)

        adapter = SysadminCliAdapter(
            client=mock_config_template_client,
            revocation_client=mock_revocation_client,
        )

        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()

        try:
            adapter.run(["revoke", "my-cred"])
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue().strip()
        assert 'Credential "my-cred" revoked' in output