#!/usr/bin/env python3
"""Main application entry point for the EC Issuer."""

from src.api.api_port import ApiPort
from src.api.http_adapter import HttpApiAdapter
from src.config.config import EnvConfigRepo
from src.config.config_port import ConfigRepoPort
from src.issuer_agent.ssi_agent_adapter import SsiAgentAdapter
from src.metadata.metadata import MetadataService


class App:
    config: ConfigRepoPort
    _api_port: ApiPort

    def __init__(self):
        self.config = EnvConfigRepo()

        issuer_agent = SsiAgentAdapter(config=self.config)
        metadata_service = MetadataService(issuer_agent=issuer_agent)

        self._api_port = HttpApiAdapter(
            config=self.config,
            metadata_service=metadata_service,
        )

    def run(self):
        self._api_port.run()


if __name__ == "__main__":
    app = App()
    app.run()
