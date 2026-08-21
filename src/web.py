#!/usr/bin/env python3
"""Main application entry point for the EC Issuer."""

from flask import Flask

from src.access_control.hardcoded_adapter import HardcodedAccessControlAdapter
from src.api.http_adapter import HttpApiAdapter
from src.awards.http_awards_client_adapter import HttpAwardsClientAdapter
from src.config.config import EnvConfigRepo
from src.config.config_port import ConfigRepoPort
from src.credential_configurations.bootstrap import resolve_credential_template_id
from src.offers.offer_service import OfferService
from src.offers.postgresql_offers_repository_adapter import (
    PostgreSQLOffersRepositoryAdapter,
)
from src.offers.ssi_agent_offers_client_adapter import SsiAgentOffersClientAdapter

class App:
    """Main application entry point."""

    config: ConfigRepoPort
    _api_port: HttpApiAdapter

    def __init__(self):
        """Initialise and wire all application dependencies."""
        # Resolve credential template ID
        credential_configuration_id = resolve_credential_template_id()

        # Create config with resolved ID
        self.config = EnvConfigRepo(
            credential_configuration_id=credential_configuration_id,
        )

        access_control = HardcodedAccessControlAdapter()

        awards_client = HttpAwardsClientAdapter(
            awards_service_url=self.config.awards_service_url,
        )

        offers_client = SsiAgentOffersClientAdapter(
            ssi_agent_url=self.config.ssi_agent_url,
            credential_template_id=self.config.credential_configuration_id,
        )
        offers_repository = PostgreSQLOffersRepositoryAdapter(
            self.config.postgresql_connection_string,
        )
        offer_service = OfferService(
            access_control=access_control,
            awards_client=awards_client,
            offers_repository=offers_repository,
            offers_client=offers_client,
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
        self._api_port.run()


def main() -> None:
    """Entry point for the EC Issuer application."""
    app = App()
    app.run()


def __getattr__(name: str):
    if name == "wsgi_app":
        return App().wsgi_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

if __name__ == "__main__":
    main()
