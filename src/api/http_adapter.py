"""HTTP REST API adapter"""

import json
from dataclasses import dataclass
from typing import override

from flask import Flask, request
from prometheus_flask_exporter import PrometheusMetrics  # pyright: ignore[reportMissingTypeStubs] PrometheusMetrics has no typing

from src.config.config_port import ConfigRepoPort
from src.metadata.metadata import HealthStatus, MetadataService
from src.offers.offer_service import OfferService, PermissionDeniedError

from .api_port import ApiPort


@dataclass
class CreateOfferBody:
    """Parsed request body for the create offer endpoint."""

    achievement_id: str


class HttpApiAdapter(ApiPort):
    """HTTP REST API adapter"""

    flask_app: Flask
    metadata_service: MetadataService
    offer_service: OfferService
    config: ConfigRepoPort

    def __init__(
        self,
        config: ConfigRepoPort,
        metadata_service: MetadataService,
        offer_service: OfferService,
    ):
        """Initialise the adapter.

        Args:
            config: Application configuration.
            metadata_service: Service for credential issuer metadata.
            offer_service: Service for creating credential offers.
        """
        self.metadata_service = metadata_service
        self.offer_service = offer_service
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

        @app.route("/api/v1/offers", methods=["POST"])
        def create_offer():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Create a credential offer for an achievement."""
            auth_header = request.headers.get("Authorization", "")
            bearer_token = auth_header.removeprefix("Bearer ").strip()

            raw: dict[str, str] = request.get_json(silent=True) or {}
            body = CreateOfferBody(achievement_id=raw.get("achievement_id", ""))

            try:
                offer = self.offer_service.create_offer(
                    achievement_id=body.achievement_id,
                    bearer_token=bearer_token,
                )
            except PermissionDeniedError:
                return json.dumps({"error": "Forbidden"}), 403

            return json.dumps({"offer_id": offer.offer_id, "uri": offer.uri}), 201

        return app

    @override
    def run(self):
        self.flask_app.run(
            host=self.config.server_host, port=self.config.server_port, debug=True
        )
