from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .support.admin_client import AdminHttpClient
from .support.http_client import Config, HttpClient
from .support.verifier import Verifier
from .support.wallet import WalletClient

_FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def seed_issuer_metadata() -> None:
    """
    Seed the database with credential issuer metadata before e2e tests run.

    We call the "sysadmin" interface, because e2e should never poke around
    in the app, and consider the app as a black box, only using its external
    interface. This sysadmin interface is crude and unfriendly to use. It
    was introduced only for the e2e tests.
    """
    _ = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "src.sysadmin.commandline_adapter",
            "update-issuer-metadata",
        ],
        input=(_FIXTURES_DIR / "issuer_metadata.json").read_bytes(),
        check=True,
    )


@pytest.fixture(scope="session")
def config() -> Config:
    """Provide test configuration.

    The ec-issuer service must be running before tests are executed.
    """
    return Config()


@pytest.fixture(scope="session")
def http_client(config: Config) -> HttpClient:
    """Provide a generic HTTP client pointed at the service under test."""
    return HttpClient(config)


@pytest.fixture(scope="session")
def admin_client(config: Config) -> AdminHttpClient:
    """Provide an admin HTTP client with auth headers."""
    return AdminHttpClient(config)


@pytest.fixture(scope="session")
def wallet_client() -> WalletClient:
    """Provide a wallet client for e2e tests."""
    return WalletClient()


@pytest.fixture(scope="session")
def verifier() -> Verifier:
    """Provide a verifier for e2e tests."""
    return Verifier()
