from __future__ import annotations

from pathlib import Path

import pytest

from .support.admin_client import AdminHttpClient
from .support.http_client import Config, HttpClient
from .support.verifier import Verifier
from .support.wallet import WalletClient

_KEYS_DIR = Path(__file__).parent / "keys"


@pytest.fixture(scope="session")
def config() -> Config:
    """Provide test configuration."""
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
