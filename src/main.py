#!/usr/bin/env python3
"""Main application entry point for the EC Issuer."""

from src.access_control.hardcoded_adapter import HardcodedAccessControlAdapter
from src.api.api_port import ApiPort
from src.api.http_adapter import HttpApiAdapter
from src.config.config import EnvConfigRepo
from src.config.config_port import ConfigRepoPort
from src.credentials.credential_service import CredentialService
from src.issuer_agent.ssi_agent_adapter import SsiAgentAdapter
from src.metadata.metadata_service import MetadataService
from src.metadata.postgresql_adapter import PostgreSQLMetadataRepository
from src.offers.offer_service import OfferService
from src.offers.postgresql_offers_repository_adapter import (
    PostgreSQLOffersRepositoryAdapter,
)
from src.offers.ssi_agent_offers_client_adapter import SsiAgentOffersClientAdapter


class App:
    """Main application entry point."""

    config: ConfigRepoPort
    _api_port: ApiPort

    def __init__(self):
        """Initialise and wire all application dependencies."""
        self.config = EnvConfigRepo()

        metadata_repository = PostgreSQLMetadataRepository(
            self.config.postgresql_connection_string
        )
        metadata_service = MetadataService(
            metadata_repository=metadata_repository, public_url=self.config.public_url
        )

        access_control = HardcodedAccessControlAdapter()

        offers_client = SsiAgentOffersClientAdapter(
            ssi_agent_url=self.config.ssi_agent_url
        )
        offers_repository = PostgreSQLOffersRepositoryAdapter(
            self.config.postgresql_connection_string
        )
        offer_service = OfferService(
            access_control=access_control,
            offers_client=offers_client,
            offers_repository=offers_repository,
        )

        credential_service = CredentialService(
            issuer_agent=SsiAgentAdapter(config=self.config)
        )

        self._api_port = HttpApiAdapter(
            config=self.config,
            metadata_service=metadata_service,
            offer_service=offer_service,
            credential_service=credential_service,
        )

    def run(self):
        self._api_port.run()


if __name__ == "__main__":
    app = App()
    app.run()
