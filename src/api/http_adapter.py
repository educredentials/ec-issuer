"""HTTP REST API adapter"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast, override

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
    OfferService,
    PermissionDeniedError,
    UnknownCredentialTypeError,
)

from .api_port import ApiPort


class MissingTokenError(Exception):
    """Raised when the Authorization header is absent or contains no token."""


@dataclass
class CreateOfferBody:
    """Parsed request body for the create offer endpoint."""

    award_id: str
    credential_type: Literal["ob3", "edc"] = "ob3"


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

    _prometheus_metrics: PrometheusMetrics
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
            credentials.  Only files under /etc/static/extensions are
            served.  The ``${BASE_URL}`` placeholder in context files
            is replaced with the value of ``EC_ISSUER_URL`` so that
            generated credentials carry the correct absolute URLs for
            their validation schemas.
            """
            if not re.match(r"^[A-Za-z0-9_-]+/(context|schema)\.json$", filename):
                return "not found", 404
            ext_dir = os.environ.get(
                "EC_ISSUER_EXTENSIONS_DIR", "/static/extensions"
            )
            base_url = os.environ.get("EC_ISSUER_URL", "http://localhost:8000")
            path = os.path.join(ext_dir, filename)
            resolved = os.path.realpath(path)
            ext_dir_real = os.path.realpath(ext_dir)
            if not resolved.startswith(ext_dir_real + os.sep):
                return "not found", 404
            if not os.path.isfile(path):
                return "not found", 404
            try:
                content = Path(path).read_text(encoding="utf-8")
            except OSError:
                return "not found", 404
            content = content.replace("${BASE_URL}", base_url)
            return content, 200, {"Content-Type": "application/ld+json"}

        @app.route("/api/v1/offers", methods=["POST"])
        def create_offer():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Create a credential offer for an achievement."""
            try:
                bearer_token = self._bearer_token(request)
            except MissingTokenError:
                return jsonify({"error": "Unauthorized"}), 401

            _raw = request.get_json(silent=True) or {}
            body = CreateOfferBody(
                award_id=cast(str, _raw.get("award_id", "")),
                credential_type=cast(
                    Literal["ob3", "edc"], _raw.get("credential_type", "ob3")
                ),
            )

            try:
                offer = self.offer_service.create_offer(
                    award_id=body.award_id,
                    bearer_token=bearer_token,
                    credential_type=body.credential_type,
                )
            except PermissionDeniedError:
                return jsonify({"error": "Forbidden"}), 403
            except UnknownCredentialTypeError as exc:
                return jsonify({"error": str(exc)}), 400

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
    def run(self):
        debug = os.environ.get("EC_ISSUER_DEBUG", "false").lower() == "true"
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
