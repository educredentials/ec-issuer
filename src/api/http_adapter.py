"""HTTP REST API adapter"""

from dataclasses import dataclass
from typing import override

import msgspec
from flask import (
    Flask,
    Request,
    jsonify,
    request,
)
from flask_cors import CORS
from prometheus_flask_exporter import (  # pyright: ignore[reportMissingTypeStubs] PrometheusMetrics has no typing
    PrometheusMetrics,
)

from src.config.config_port import ConfigRepoPort
from src.offers.offer_service import (
    NotFoundError,
    OfferService,
    OfferServiceError,
    PermissionDeniedError,
    UnknownCredentialTypeError,
)

from .api_port import ApiPort
from .extension_context_server import ExtensionContextServer


class MissingTokenError(Exception):
    """Raised when the Authorization header is absent or contains no token."""


@dataclass
class CreateOfferBody:
    """Parsed request body for the create offer endpoint."""

    award_id: str
    credential_type: str = "ob3"


class HttpApiAdapter(ApiPort):
    """HTTP REST API adapter"""

    _prometheus_metrics: PrometheusMetrics
    flask_app: Flask
    offer_service: OfferService
    config: ConfigRepoPort
    _extension_context_server: ExtensionContextServer

    def __init__(
        self,
        config: ConfigRepoPort,
        offer_service: OfferService,
    ):
        """Initialise the adapter.

        Args:
            config: Application configuration.
            offer_service: Service for creating credential offers.
        """
        self.offer_service = offer_service
        self.config = config
        self._extension_context_server = ExtensionContextServer(
            base_url=config.ec_issuer_url,
            extensions_dir=config.ec_issuer_extensions_dir,
        )
        self.flask_app = self._flask_app()

    def _flask_app(self) -> Flask:
        app = Flask("HttpApi")

        # Configure CORS
        allowed_origins = self._parse_allowed_cors_domains()
        _ = CORS(app, resources={r"/*": {"origins": allowed_origins}})

        # Metrics endpoint is only relevant to HttpAdapter
        # no need for service/domain models
        self._prometheus_metrics = PrometheusMetrics(app)
        # PrometheusMetrics has no typing

        @app.route("/health")
        @self._prometheus_metrics.do_not_track()
        def health() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Health check endpoint."""
            return "OK"

        @app.route("/")
        def root() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Root endpoint."""
            return "Hello, World!"

        @app.route("/static/extensions/<path:filename>")
        def serve_extension_context(filename: str):  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Serve JSON-LD extension contexts from static/extensions/.

            SSI agents dereference these @context URLs when validating
            credentials.  Only files under the configured extensions
            directory are served.
            """
            content, status_code, headers = self._extension_context_server.serve(
                filename
            )
            return content, status_code, headers

        @app.route("/api/v1/offers", methods=["POST"])
        def create_offer():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Create a credential offer for an achievement."""
            try:
                bearer_token = self._bearer_token(request)
            except MissingTokenError:
                return jsonify({"error": "Unauthorized"}), 401

            try:
                body: CreateOfferBody = msgspec.json.decode(  # type: ignore[return-value]
                    request.get_data(),
                    type=CreateOfferBody,
                )
            except (msgspec.ValidationError, msgspec.DecodeError):
                return jsonify({"error": "Missing or invalid request body"}), 400

            try:
                offer = self.offer_service.create_offer(
                    award_id=body.award_id,
                    bearer_token=bearer_token,
                    credential_type=body.credential_type,
                )
            except NotFoundError as exc:
                return jsonify({"error": str(exc)}), 404
            except PermissionDeniedError:
                return jsonify({"error": "Forbidden"}), 403
            except UnknownCredentialTypeError as exc:
                return jsonify({"error": str(exc)}), 400
            except OfferServiceError as exc:
                return jsonify({"error": str(exc)}), 502

            return jsonify({"offer_id": offer.offer_id, "uri": offer.uri}), 201

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
    def run(self) -> None:
        """Start the HTTP API server."""
        debug = self.config.debug
        self.flask_app.run(
            host=self.config.server_host, port=self.config.server_port, debug=debug
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
