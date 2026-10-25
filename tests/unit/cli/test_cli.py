from unittest.mock import MagicMock, patch
from typing import cast

from src.cli import App
from src.sysadmin.sysadmin_cli_adapter import SysadminCliAdapter


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