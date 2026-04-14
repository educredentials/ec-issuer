"""HTTP REST API adapter"""

import json
from typing import override

from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics  # pyright: ignore[reportMissingTypeStubs] PrometheusMetrics has no typing

from src.config.config_port import ConfigRepoPort
from src.metadata.metadata import HealthStatus, MetadataService

from .api_port import ApiPort


class HttpApiAdapter(ApiPort):
    """HTTP REST API adapter"""

    flask_app: Flask
    metadata_service: MetadataService
    config: ConfigRepoPort

    def __init__(self, config: ConfigRepoPort, metadata_service: MetadataService):
        self.metadata_service = metadata_service
        self.config = config
        self.flask_app = self._flask_app()

    def _flask_app(self) -> Flask:
        app = Flask("HttpApi")

        # Metrics endpoint is only relevant to HttpAdapter
        # no need for service/domain models
        metrics: PrometheusMetrics = PrometheusMetrics(app)
        _ = metrics.info('app_info', 'Application info', version='1.0.3')  # pyright: ignore[reportUnknownMemberType] PrometheusMetrics has no typing

        @app.route("/health")
        @metrics.do_not_track()
        def health() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Health check endpoint."""
            health = self.metadata_service.get_health()
            if health == HealthStatus.HEALTHY:
                return "OK"
            else:
                return "NOT OK"

        @app.route("/")
        def root() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Root endpoint."""
            return "Hello, World!"

        @app.route("/.well-known/openid-credential-issuer")
        def credential_issuer_metadata() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Credential Issuer Metadata endpoint."""
            metadata = self.metadata_service.get_credential_issuer_metadata()
            return json.dumps(metadata.__dict__)

        return app

    @override
    def run(self):
        self.flask_app.run(
            host=self.config.server_host, port=self.config.server_port, debug=True
        )
