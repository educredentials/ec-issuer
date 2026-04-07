"""HTTP REST API adapter"""

import json
from typing import override

from flask import Flask

from src.config import ConfigRepo
from src.metadata import HealthStatus, MetadataService

from . import ApiPort


class HttpApiAdapter(ApiPort):
    """HTTP REST API adapter"""

    flask_app: Flask
    metadata_service: MetadataService
    config: ConfigRepo

    def __init__(self, config: ConfigRepo, metadata_service: MetadataService):
        self.metadata_service = metadata_service
        self.config = config
        self.flask_app = self._flask_app()

    def _flask_app(self) -> Flask:
        app = Flask("HttpApi")

        @app.route("/health")
        def health() -> str:
            """Health check endpoint."""
            health = self.metadata_service.get_health()
            if health == HealthStatus.HEALTHY:
                return "OK"
            else:
                return "NOT OK"

        @app.route("/")
        def root() -> str:
            """Root endpoint."""
            return "Hello, World!"

        @app.route("/.well-known/openid-credential-issuer")
        def credential_issuer_metadata() -> str:
            """Credential Issuer Metadata endpoint."""
            metadata = self.metadata_service.get_credential_issuer_metadata()
            return json.dumps(metadata.__dict__)

        _ = health()
        _ = root()
        _ = credential_issuer_metadata()

        return app

    @override
    def run(self):
        self.flask_app.run(
            host=self.config.server_host, port=self.config.server_port, debug=True
        )
