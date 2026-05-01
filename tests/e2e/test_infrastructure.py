"""End-to-end tests for infrastructure endpoints."""

import pytest

from tests.e2e.support.http_client import HttpClient


@pytest.mark.e2e
class TestHealthEndpoint:
    """Test the health endpoint."""

    def test_health_success(self, http_client: HttpClient):
        """Test that the health endpoint returns OK."""
        response = http_client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"


@pytest.mark.e2e
class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_endpoint(self, http_client: HttpClient):
        """Test that the root endpoint returns Hello, World!."""
        response = http_client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"


@pytest.mark.e2e
class TestMetricsEndpoint:
    """Test the Prometheus metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_metrics(self, http_client: HttpClient):
        """Test that /metrics endpoint returns Prometheus metrics after requesting /."""
        response = http_client.get("/")
        assert response.status_code == 200

        response = http_client.get("/metrics")
        assert response.status_code == 200

        text = response.text
        assert 'flask_http_request_total{method="GET",status="200"}' in text
        assert (
            "TYPE" in text
            or "COUNTER" in text
            or "GAUGE" in text
            or "HISTOGRAM" in text
            or "SUMMARY" in text
        )
