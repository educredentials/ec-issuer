"""Unit tests for the API Port HTTP Adapter - aka the Flask app"""

from typing import override

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

    def test_offers_unsupported_credential_type_raises_exception(self):
        """POST /api/v1/offers with unrecognized credential_type raises.

        The service layer (and Literal type gate) rejects unsupported values.
        In production a Flask error handler should map this to 400.
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
        with pytest.raises(
            UnknownCredentialTypeError, match="Unsupported credential_type"
        ):
            _ = http_client.post(
                "/api/v1/offers",
                headers={"Authorization": "Bearer t0k3n"},
                json={"award_id": "achievement-1", "credential_type": "foobar"},
            )
