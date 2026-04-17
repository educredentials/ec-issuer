"""Unit tests for the API Port HTTP Adapter - aka the Flask app"""

from flask.testing import FlaskClient

from tests.unit.api.conftest import setup_http_client
from tests.unit.test_doubles import DenyingOfferServiceStub, OfferServiceSpy


class TestHttpAdapter:
    """Tests for HttpApiAdapter routes."""

    def test_root(self, http_client: FlaskClient):
        """GET / returns Hello, World!."""
        response = http_client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"

    def test_offers_creates_offer_and_returns_201(
        self, http_client: FlaskClient, offer_service_spy: OfferServiceSpy
    ):
        """POST /api/v1/offers with valid auth returns 201 and records the call."""
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"achievement_id": "achievement-1"},
        )
        assert response.status_code == 201
        assert ("create_offer", "achievement-1", "t0k3n") in offer_service_spy.calls

    def test_offers_missing_authorization_header_returns_401(
        self, http_client: FlaskClient
    ):
        """POST /api/v1/offers without Authorization header returns 401."""
        response = http_client.post(
            "/api/v1/offers",
            json={"achievement_id": "achievement-1"},
        )
        assert response.status_code == 401

    def test_offers_empty_bearer_token_returns_401(self, http_client: FlaskClient):
        """POST /api/v1/offers with empty bearer token returns 401."""
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer "},
            json={"achievement_id": "achievement-1"},
        )
        assert response.status_code == 401

    def test_offers_permission_denied_returns_403(self):
        """POST /api/v1/offers returns 403 when PermissionDeniedError is raised."""
        denying_offer_service = DenyingOfferServiceStub()
        denying_http_client: FlaskClient = setup_http_client(denying_offer_service)
        response = denying_http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"achievement_id": "achievement-1"},
        )
        assert response.status_code == 403
