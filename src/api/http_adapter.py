"""HTTP REST API adapter"""

import json
from dataclasses import dataclass
from typing import override
from urllib.parse import urlparse

import msgspec
from flask import Flask, Request, request
from prometheus_flask_exporter import PrometheusMetrics  # pyright: ignore[reportMissingTypeStubs] PrometheusMetrics has no typing

from src.config.config_port import ConfigRepoPort
from src.credentials.credential_service import CredentialService
from src.issuer_agent.issuer_agent_port import IssuerAgentError
from src.metadata.metadata_service import HealthStatus, MetadataService
from src.offers.offer_service import OfferService, PermissionDeniedError

from .api_port import ApiPort


class MissingTokenError(Exception):
    """Raised when the Authorization header is absent or contains no token."""


@dataclass
class CreateOfferBody:
    """Parsed request body for the create offer endpoint."""

    achievement_id: str


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
    metadata_service: MetadataService
    offer_service: OfferService
    credential_service: CredentialService
    config: ConfigRepoPort

    def __init__(
        self,
        config: ConfigRepoPort,
        metadata_service: MetadataService,
        offer_service: OfferService,
        credential_service: CredentialService,
    ):
        """Initialise the adapter.

        Args:
            config: Application configuration.
            metadata_service: Service for credential issuer metadata.
            offer_service: Service for creating credential offers.
            credential_service: Service for requesting credentials.
        """
        self.metadata_service = metadata_service
        self.offer_service = offer_service
        self.credential_service = credential_service
        self.config = config
        self.flask_app = self._flask_app()

    def _flask_app(self) -> Flask:
        app = Flask("HttpApi")

        # Metrics endpoint is only relevant to HttpAdapter
        # no need for service/domain models
        metrics: PrometheusMetrics = PrometheusMetrics(app)
        _ = metrics.info("app_info", "Application info", version="1.0.3")  # pyright: ignore[reportUnknownMemberType] PrometheusMetrics has no typing

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
            # msgspec encodes the metadata to JSON, as bytes, so we decode to a string
            return msgspec.json.encode(metadata).decode()

        @app.route("/.well-known/did.json")
        def did_document() -> str:  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """DID document endpoint for the issuer."""
            # Get the public URL from config
            public_url = self.config.public_url
            # Parse the URL to extract host and port
            parsed = urlparse(public_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            
            # Create DID from host and port
            # For DID Web, only the port colon needs to be percent-encoded
            # did:web: uses literal colons, but the port separator : needs to be %3A
            did = f"did:web:{host}%3A{port}"
            
            # The public key is hardcoded for now
            # In production this would come from the agent
            did_document = {
                "@context": ["https://www.w3.org/ns/did/v1", "https://w3id.org/security/suites/ed25519-2020/v1"],
                "id": did,
                "verificationMethod": [
                    {
                        "id": f"{did}#key-1",
                        "type": "Ed25519VerificationKey2020",
                        "controller": did,
                        "publicKeyPem": (
                    "-----BEGIN PUBLIC KEY-----\n"
                    "MCowBQYDK2VwAyEAX4FOGLXPUOD06/9ygJ1wyZX+qreCuuZu3xl/rB4OJXA=\n"
                    "-----END PUBLIC KEY-----"
                )
                    }
                ],
                "authentication": [f"{did}#key-1"],
                "assertionMethod": [f"{did}#key-1"]
            }
            return msgspec.json.encode(did_document).decode()

        @app.route("/api/v1/offers/<offer_id>", methods=["GET"])
        def get_offer(offer_id: str):  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Return a credential offer by its identifier."""
            try:
                offer = self.offer_service.get_offer(offer_id)
            except KeyError:
                return json.dumps({"error": "Not Found"}), 404

            return json.dumps(offer.to_credential_offer()), 200

        @app.route("/api/v1/offers", methods=["POST"])
        def create_offer():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Create a credential offer for an achievement."""
            try:
                bearer_token = self._bearer_token(request)
            except MissingTokenError:
                return json.dumps({"error": "Unauthorized"}), 401

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

        @app.route("/credential", methods=["POST"])
        def request_credential():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Request a credential from the issuer."""
            try:
                access_token = self._bearer_token(request)
            except MissingTokenError:
                return json.dumps({"error": "Unauthorized"}), 401

            raw_json = request.get_data(as_text=True)

            try:
                body: CredentialRequestBody = msgspec.json.decode(
                    raw_json, type=CredentialRequestBody
                )
                credential_response = self.credential_service.request_credential(
                    format=body.format,
                    credential_configuration_id=body.credential_configuration_id,
                    proof={"proof_type": body.proof.proof_type, "jwt": body.proof.jwt},
                    issuer_state=body.issuer_state,
                    access_token=access_token,
                )
            except msgspec.ValidationError as e:
                return json.dumps({"error": str(e)}), 400
            except IssuerAgentError as e:
                return json.dumps({"error": str(e)}), 502

            return msgspec.json.encode(credential_response).decode(), 200

        @app.route("/nonce", methods=["POST"])
        def request_nonce():  # pyright: ignore[reportUnusedFunction] Flask decorators aren't called by design
            """Request a nonce from the issuer agent."""
            try:
                nonce_response = self.credential_service.request_nonce()
            except IssuerAgentError as e:
                return json.dumps({"error": str(e)}), 502

            return msgspec.json.encode(nonce_response).decode(), 200

        return app

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
