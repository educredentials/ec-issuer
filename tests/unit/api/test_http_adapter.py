"""Unit tests for the API Port HTTP Adapter - aka the Flask app"""

import os
from pathlib import Path
from typing import cast, override

import pytest
from flask.testing import FlaskClient

from src.offers.models import Offer
from src.offers.offer_service import UnknownCredentialTypeError

from ..api.conftest import setup_http_client
from ..support.test_doubles import DenyingOfferServiceStub, OfferServiceSpy


class TestHttpAdapter:
    """Tests for HttpApiAdapter routes."""

    def test_root(self, http_client: FlaskClient):
        """GET / returns Hello, World!."""
        response = http_client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"

    def test_root_returns_cors_headers(self, http_client: FlaskClient):
        """GET / returns CORS headers."""
        response = http_client.get("/")
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        # The ConfigRepoStub has ALLOWED_CORS_DOMAINS="http://localhost:8000,https://app.example.com"
        # Flask-CORS will use the first origin for simple requests
        assert (
            response.headers["Access-Control-Allow-Origin"] == "http://localhost:8000"
        )

    def test_offers_creates_offer_and_returns_201(
        self, http_client: FlaskClient, offer_service_spy: OfferServiceSpy
    ):
        """POST /api/v1/offers with valid auth returns 201 and records the call."""
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"award_id": "achievement-1"},
        )
        assert response.status_code == 201
        assert (
            "create_offer",
            "achievement-1",
            "t0k3n",
            "ob3",
        ) in offer_service_spy.calls

    def test_offers_missing_authorization_header_returns_401(
        self, http_client: FlaskClient
    ):
        """POST /api/v1/offers without Authorization header returns 401."""
        response = http_client.post(
            "/api/v1/offers",
            json={"award_id": "achievement-1"},
        )
        assert response.status_code == 401

    def test_offers_empty_bearer_token_returns_401(self, http_client: FlaskClient):
        """POST /api/v1/offers with empty bearer token returns 401."""
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer "},
            json={"award_id": "achievement-1"},
        )
        assert response.status_code == 401

    def test_offers_permission_denied_returns_403(self):
        """POST /api/v1/offers returns 403 when PermissionDeniedError is raised."""
        denying_offer_service = DenyingOfferServiceStub()
        denying_http_client: FlaskClient = setup_http_client(denying_offer_service)
        response = denying_http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"award_id": "achievement-1"},
        )
        assert response.status_code == 403

    def test_offers_edc_credential_type_passes_edc_to_service(
        self, http_client: FlaskClient, offer_service_spy: OfferServiceSpy
    ):
        """POST /api/v1/offers with credential_type='edc' dispatches to EDC path."""
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"award_id": "achievement-1", "credential_type": "edc"},
        )
        assert response.status_code == 201
        calls = offer_service_spy.calls
        assert len(calls) == 1
        call = calls[0]
        assert call[0] == "create_offer"
        assert call[3] == "edc"

    def test_offers_unsupported_credential_type_returns_400(self):
        """POST /api/v1/offers with unrecognized credential_type returns 400.

        The service layer rejects unsupported values and the Flask error
        handler maps UnknownCredentialTypeError to a 400 response.
        """

        class _UnsupportedCredentialTypeService(OfferServiceSpy):
            @override
            def create_offer(
                self,
                award_id: str,
                bearer_token: str,
                *,
                credential_type: str = "ob3",
            ) -> Offer:
                raise UnknownCredentialTypeError(
                    "Unsupported credential_type: "
                    + f"{credential_type!r}. "
                    + "Must be 'ob3' or 'edc'."
                )

        service = _UnsupportedCredentialTypeService()
        http_client = setup_http_client(service)
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"award_id": "achievement-1", "credential_type": "foobar"},
        )
        assert response.status_code == 400
        body = cast(dict[str, str], response.get_json(force=True))
        assert "error" in body
        assert "Unsupported credential_type" in body["error"]


class TestServeExtensionContext:
    """Tests for the /static/extensions/<path:filename> route."""

    @pytest.fixture(autouse=True)
    def _set_extensions_dir(self):
        """Point EC_ISSUER_EXTENSIONS_DIR at the project's static/extensions/."""
        old = os.environ.get("EC_ISSUER_EXTENSIONS_DIR")
        os.environ["EC_ISSUER_EXTENSIONS_DIR"] = str(
            Path(__file__).resolve().parents[3] / "static" / "extensions"
        )
        yield
        if old is None:
            _ = os.environ.pop("EC_ISSUER_EXTENSIONS_DIR", None)
        else:
            os.environ["EC_ISSUER_EXTENSIONS_DIR"] = old

    def test_serves_context_json(self, http_client: FlaskClient):
        """GET a context.json file returns 200 with ld+json content type."""
        response = http_client.get(
            "/static/extensions/LanguageExtension/context.json"
        )
        assert response.status_code == 200
        assert response.content_type == "application/ld+json"

    def test_serves_schema_json(self, http_client: FlaskClient):
        """GET a schema.json file returns 200 with ld+json content type."""
        response = http_client.get(
            "/static/extensions/LanguageExtension/schema.json"
        )
        assert response.status_code == 200
        assert response.content_type == "application/ld+json"

    def test_replaces_base_url_placeholder_in_context(self, http_client: FlaskClient):
        """The ${BASE_URL} placeholder is replaced with EC_ISSUER_URL."""
        old_url = os.environ.get("EC_ISSUER_URL")
        os.environ["EC_ISSUER_URL"] = "https://edu.example.com"
        try:
            response = http_client.get(
                "/static/extensions/LanguageExtension/context.json"
            )
            assert response.status_code == 200
            body = cast(dict[str, object], response.get_json())
            validation = cast(
                list[dict[str, object]], body.get("obi:validation") or []
            )
            schema_url = cast(
                str, validation[0].get("obi:validationSchema")
            )
            assert schema_url == "https://edu.example.com/static/extensions/LanguageExtension/schema.json"
        finally:
            if old_url is None:
                _ = os.environ.pop("EC_ISSUER_URL", None)
            else:
                os.environ["EC_ISSUER_URL"] = old_url

    def test_falls_back_to_default_when_env_unset(self, http_client: FlaskClient):
        """Default BASE_URL is http://localhost:8000."""
        _ = os.environ.pop("EC_ISSUER_URL", None)
        response = http_client.get(
            "/static/extensions/LanguageExtension/context.json"
        )
        assert response.status_code == 200
        body = cast(dict[str, object], response.get_json())
        validation = cast(
            list[dict[str, object]], body.get("obi:validation") or []
        )
        schema_url = cast(
            str, validation[0].get("obi:validationSchema")
        )
        assert schema_url == "http://localhost:8000/static/extensions/LanguageExtension/schema.json"

    def test_returns_404_for_invalid_path(self, http_client: FlaskClient):
        """Invalid paths return 404."""
        response = http_client.get("/static/extensions/../../../etc/passwd")
        assert response.status_code == 404

    def test_returns_404_for_nonexistent_extension(self, http_client: FlaskClient):
        """Non-existent extension directories return 404."""
        response = http_client.get(
            "/static/extensions/NonExistentExtension/context.json"
        )
        assert response.status_code == 404
