#!/usr/bin/env python3
"""Main application entry point for the EC Issuer."""

from flask import Flask
from src.config import Config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    @app.route("/health")
    def health() -> str:
        """Health check endpoint."""
        return "OK"

    @app.route("/")
    def root() -> str:
        """Root endpoint."""
        return "Hello, World!"

    return app


if __name__ == "__main__":
    app = create_app()
    config = Config.from_env()
    app.run(host=config.server_host, port=config.server_port, debug=True)
