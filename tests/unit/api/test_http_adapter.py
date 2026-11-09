"""Unit tests for the API Port HTTP Adapter - aka the Flask app"""

from typing import cast, override

import pytest
from flask.testing import FlaskClient

from src.offers.models import Offer
from src.offers.offer_service import (
    NotFoundError,
    OfferServiceError,
    UnknownCredentialTypeError,
)

from ..api.conftest import setup_http_client
from ..support.test_doubles import (
    DenyingOfferServiceStub,
    OfferServiceSpy,
    UnhealthyOfferServiceStub,
)


class _RaisingOfferServiceSpy(OfferServiceSpy):
    """OfferServiceSpy whose create_offer always raises the given error."""

    def __init__(self, error: Exception) -> None:
        """Initialize with the error to raise on create_offer."""
        super().__init__()
        self._error = error

    @override
    def create_offer(
        self,
        award_id: str,
        bearer_token: str,
        *,
        credential_type: str = "ob3",
    ) -> Offer:
        """Raise the configured error."""
        raise self._error


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

    @pytest.mark.parametrize(
        "headers",
        [
            pytest.param(None, id="missing-authorization-header"),
            pytest.param({"Authorization": "Bearer "}, id="empty-bearer-token"),
        ],
    )
    def test_offers_unauthorized_returns_401(
        self,
        http_client: FlaskClient,
        headers: dict[str, str] | None,
    ):
        """POST /api/v1/offers without a valid bearer token returns 401."""
        response = http_client.post(
            "/api/v1/offers",
            headers=headers,
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

    @pytest.mark.parametrize(
        ("error", "status", "error_fragment"),
        [
            pytest.param(
                UnknownCredentialTypeError(
                    "Unsupported credential_type: 'foobar'. Must be 'ob3' or 'edc'."
                ),
                400,
                "Unsupported credential_type",
                id="unknown-credential-type-400",
            ),
            pytest.param(
                NotFoundError("Award missing-award not found"),
                404,
                "not found",
                id="missing-award-404",
            ),
            pytest.param(
                OfferServiceError("Upstream unavailable"),
                502,
                "Upstream unavailable",
                id="service-error-502",
            ),
        ],
    )
    def test_offers_service_errors_map_to_status(
        self,
        error: Exception,
        status: int,
        error_fragment: str,
    ):
        """Offer service exceptions map to their HTTP status and message."""
        client = setup_http_client(_RaisingOfferServiceSpy(error))
        response = client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={"award_id": "achievement-1"},
        )
        assert response.status_code == status
        body = cast(dict[str, str], response.get_json(force=True))
        assert error_fragment in body["error"]

    def test_offers_malformed_body_returns_400(self, http_client: FlaskClient):
        """POST /api/v1/offers returns 400 for malformed JSON body."""
        response = http_client.post(
            "/api/v1/offers",
            headers={
                "Authorization": "Bearer t0k3n",
                "Content-Type": "application/json",
            },
            data=b"{not valid json}",
        )
        assert response.status_code == 400

    def test_offers_missing_award_id_returns_400(self, http_client: FlaskClient):
        """POST /api/v1/offers returns 400 when award_id is missing."""
        response = http_client.post(
            "/api/v1/offers",
            headers={"Authorization": "Bearer t0k3n"},
            json={},
        )
        assert response.status_code == 400

    def test_health_returns_200_when_db_healthy(self, http_client: FlaskClient):
        """GET /health returns 200 with healthy DB status."""
        response = http_client.get("/health")
        assert response.status_code == 200
        body = cast(dict[str, str], response.get_json(force=True))
        assert body["status"] == "healthy"
        assert body["database"] == "ok"

    def test_health_returns_503_when_db_unhealthy(self):
        """GET /health returns 503 when database is unreachable."""
        unhealthy_service = UnhealthyOfferServiceStub()
        unhealthy_http_client: FlaskClient = setup_http_client(unhealthy_service)
        response = unhealthy_http_client.get("/health")
        assert response.status_code == 503
        body = cast(dict[str, str], response.get_json(force=True))
        assert body["status"] == "unhealthy"
        assert body["database"] == "error"


class TestServeExtensionContext:
    """Tests for the /static/extensions/<path:filename> route."""

    @pytest.mark.parametrize("filename", ["context.json", "schema.json"])
    def test_serves_extension_json(
        self, http_client: FlaskClient, filename: str
    ):
        """GET an extension JSON file returns 200 with ld+json content type."""
        response = http_client.get(
            f"/static/extensions/v1/LanguageExtension/{filename}"
        )
        assert response.status_code == 200
        assert response.content_type == "application/ld+json"

    def test_replaces_base_url_placeholder_in_context(self, http_client: FlaskClient):
        """The ${BASE_URL} placeholder is replaced with the configured URL."""
        response = http_client.get(
            "/static/extensions/v1/LanguageExtension/context.json"
        )
        assert response.status_code == 200
        body = cast(dict[str, object], response.get_json())
        validation = cast(
            list[dict[str, object]], body.get("obi:validation") or []
        )
        schema_url = cast(
            str, validation[0].get("obi:validationSchema")
        )
        assert schema_url == "http://localhost:8000/static/extensions/v1/LanguageExtension/schema.json"

    def test_returns_404_for_invalid_path(self, http_client: FlaskClient):
        """Invalid paths return 404."""
        response = http_client.get("/static/extensions/../../../etc/passwd")
        assert response.status_code == 404

    def test_returns_404_for_nonexistent_extension(self, http_client: FlaskClient):
        """Non-existent extension directories return 404."""
        response = http_client.get(
            "/static/extensions/v1/NonExistentExtension/context.json"
        )
        assert response.status_code == 404
