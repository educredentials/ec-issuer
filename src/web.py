#!/usr/bin/env python3
"""Main application entry point for the EC Issuer."""

import atexit
import sys
from flask import Flask

from src.access_control.hardcoded_adapter import HardcodedAccessControlAdapter
from src.api.http_adapter import HttpApiAdapter
from src.awards.http_awards_client_adapter import HttpAwardsClientAdapter
from src.config.config import EnvConfigRepo
from src.config.config_port import ConfigRepoPort
from src.credential_configurations.bootstrap import resolve_credential_template_ids
from src.credential_converter.http_adapter import HttpCredentialConverterAdapter
from src.offers.offer_service import OfferService
from src.offers.offers_repository_port import OffersRepositoryPort
from src.offers.postgresql_offers_repository_adapter import (
    PostgreSQLOffersRepositoryAdapter,
)
from src.offers.ssi_agent_offers_client_adapter import SsiAgentOffersClientAdapter


class App:
    """Main application entry point."""

    config: ConfigRepoPort
    _api_port: HttpApiAdapter
    offers_repository: OffersRepositoryPort

    def __init__(self):
        """Initialise and wire all application dependencies."""
        # Resolve credential template IDs (supports multiple from a directory)
        credential_configuration_ids = resolve_credential_template_ids()

        # Create config with resolved IDs
        self.config = EnvConfigRepo(
            credential_configuration_ids=credential_configuration_ids,
        )

        access_control = HardcodedAccessControlAdapter()

        awards_client = HttpAwardsClientAdapter(
            awards_service_url=self.config.awards_service_url,
        )

        offers_client = SsiAgentOffersClientAdapter(
            ssi_agent_url=self.config.ssi_agent_url,
            credential_template_ids=self.config.credential_configuration_ids,
            edc_ssi_agent_url=self.config.edc_ssi_agent_url,
        )
        offers_repository = PostgreSQLOffersRepositoryAdapter(
            self.config.postgresql_connection_string,
        )
        self.offers_repository = offers_repository

        offer_service = OfferService(
            access_control=access_control,
            awards_client=awards_client,
            offers_repository=offers_repository,
            offers_client=offers_client,
            credential_converter=HttpCredentialConverterAdapter(
                converter_base_url=self.config.credential_converter_url,
            ),
        )

        api_adapter = HttpApiAdapter(
            config=self.config,
            offer_service=offer_service,
        )
        self._api_port = api_adapter

    @property
    def wsgi_app(self) -> Flask:
        """WSGI application, for use with gunicorn."""
        return self._api_port.flask_app

    def run(self):
        """Start the application."""
        # Monkey-patch psycopg_pool for Python 3.14 shutdown safety.
        # Runs early so every pool instance inherits the safe __del__.
        if sys.version_info >= (3, 14):
            from psycopg_pool.pool import ConnectionPool

            _orig = ConnectionPool.__del__

            def _safe(_self) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
                if not sys.is_finalizing():
                    _orig(_self)

            ConnectionPool.__del__ = _safe  # pyright: ignore[reportAttributeAccessIssue]
        self._api_port.run()


def _shutdown() -> None:
    """Close the repository gracefully before interpreter exit."""
    try:
        if "_app" not in globals():
            return  # pdoc or similar tools may import without full init
        _app.offers_repository.close()
    except Exception:
        # Best-effort: gunicorn workers may not run atexit during
        # graceful shutdown; the pool closes on its own eventually.
        pass


_ = atexit.register(_shutdown)

# Guard psycopg_pool.__del__ against Python 3.14's stricter finalization.
# During interpreter shutdown, psycopg_pool.__del__ tries to join() internal
# threads with a 5s timeout, but join() is not allowed during finalization
# (raises PythonFinalizationError).  Skip it — the pool is already closing.
if sys.version_info >= (3, 14):
    from psycopg_pool.pool import ConnectionPool

    _orig_pool_del = ConnectionPool.__del__

    def _safe_pool_del(_self) -> None:  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
        if not sys.is_finalizing():
            _orig_pool_del(_self)

    ConnectionPool.__del__ = _safe_pool_del  # pyright: ignore[reportAttributeAccessIssue]


def main() -> None:
    """Entry point for the EC Issuer application."""
    app = App()
    app.run()


def __getattr__(name: str):
    global _app
    if name == "wsgi_app":
        _app = App()  # lazy: only instantiated when gunicorn accesses wsgi_app
        return _app.wsgi_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    main()
