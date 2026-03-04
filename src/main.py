#!/usr/bin/env python3
"""Main application entry point for the EC Issuer."""

from flask import Flask, Response, jsonify, request

from src.config import EnvConfigRepo
from src.issuer_agent_adapter import IssuerAgentAdapter
from src.issuer_agent_adapter.proxy_adapter import ProxyIssuerAgentAdapter


def create_app(issuer_agent_adapter: IssuerAgentAdapter) -> Flask:
    """Create and configure the Flask application.

    Args:
        issuer_agent_adapter: The adapter to use for the issuer agent.
    """
    app = Flask(__name__)

    @app.route("/health")
    def health() -> str:
        """Health check endpoint."""
        return "OK"

    @app.route("/")
    def root() -> str:
        """Root endpoint."""
        return "Hello, World!"

    @app.route("/.well-known/openid-credential-issuer")
    def credential_issuer_metadata() -> Response:
        """Credential Issuer Metadata endpoint."""
        response = issuer_agent_adapter.credential_issuer_metadata(
            request  # type: ignore[arg-type]
        )
        flask_response = jsonify(response.json())
        flask_response.status_code = response.status_code
        return flask_response

    return app


if __name__ == "__main__":
    config = EnvConfigRepo()
    app = create_app(ProxyIssuerAgentAdapter(config=config))
    app.run(host=config.server_host, port=config.server_port, debug=True)
