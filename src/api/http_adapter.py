"""HTTP REST API adapter"""

import json
from dataclasses import dataclass
from typing import override

from flask import Flask, Request, request
from flask_cors import CORS
from prometheus_flask_exporter import (  # pyright: ignore[reportMissingTypeStubs] PrometheusMetrics has no typing
    PrometheusMetrics,
)

from src.config.config_port import ConfigRepoPort
from src.offers.offer_service import OfferService, PermissionDeniedError

from .api_port import ApiPort


class MissingTokenError(Exception):
    """Raised when the Authorization header is absent or contains no token."""


@dataclass
class CreateOfferBody:
    """Parsed request body for the create offer endpoint."""

    award_id: str


@dataclass
class Proof:
    """Proof object for credential request."""

    proof_type: str
    jwt: str


@dataclass
class CredentialRequestBody:
    """Parsed request body for the credential endpoint."""

    format: str
    credential_configuration_id: str
    proof: Proof
    issuer_state: str


class HttpApiAdapter(ApiPort):
    """HTTP REST API adapter"""

    flask_app: Flask
    offer_service: OfferService
    config: ConfigRepoPort

    def __init__(
        self,
        config: ConfigRepoPort,
        offer_service: OfferService,
    ):
        """Initialise the adapter.

        Args:
            config: Application configuration.
            metadata_service: Service for credential issuer metadata.
            offer_service: Service for creating credential offers.
            credential_service: Service for requesting credentials.
        """
        self.offer_service = offer_service
        self.config = config
        self.flask_app = self._flask_app()

    def _flask_app(self) -> Flask:
        app = Flask("HttpApi")

        # Configure CORS
        allowed_origins = self._parse_allowed_cors_domains()
        _ = CORS(app, resources={r"/*": {"origins": allowed_origins}})

        # Metrics endpoint is only relevant to HttpAdapter
        # no need for service/domain models
        metrics: PrometheusMetrics = PrometheusMetrics(app)
        _ = metrics.info("app_info", "Application info", version="1.0.3")  # pyright: ignore[reportUnknownMemberType] PrometheusMetrics has no typing

        @app.route("/health")
        @metrics.do_not_track()
        def health() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Health check endpoint."""
            return "OK"

        @app.route("/")
        def root() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Root endpoint."""
            return "Hello, World!"

        @app.route("/api/v1/offers", methods=["POST"])
        def create_offer():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Create a credential offer for an achievement."""
            try:
                bearer_token = self._bearer_token(request)
            except MissingTokenError:
                return json.dumps({"error": "Unauthorized"}), 401

            raw: dict[str, str] = request.get_json(silent=True) or {}
            body = CreateOfferBody(award_id=raw.get("award_id", ""))

            try:
                offer = self.offer_service.create_offer(
                    award_id=body.award_id,
                    bearer_token=bearer_token,
                )
            except PermissionDeniedError:
                return json.dumps({"error": "Forbidden"}), 403

            return json.dumps({"offer_id": offer.offer_id, "uri": offer.uri}), 201

        return app

    def _parse_allowed_cors_domains(self) -> list[str]:
        """Parse the allowed CORS domains from configuration.

        Returns:
            List of allowed origins. If the config value is "*", returns ["*"].
            Otherwise, splits the comma-separated list of domains.
        """
        domains = self.config.allowed_cors_domains
        if domains == "*":
            return ["*"]
        return [domain.strip() for domain in domains.split(",")]

    @override
    def run(self):
        self.flask_app.run(
            host=self.config.server_host, port=self.config.server_port, debug=True
        )

    def _bearer_token(self, request: Request) -> str:
        """Extract the bearer token from the Authorization header.

        Args:
            request: The incoming Flask request.

        Returns:
            The bearer token string.

        Raises:
            MissingTokenError: When the header is absent or the token is empty.
        """
        auth_header = request.authorization
        if not auth_header or not auth_header.token:
            raise MissingTokenError()
        return auth_header.token
