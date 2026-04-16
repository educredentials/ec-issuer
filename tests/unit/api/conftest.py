"""Fixtures for HttpApiAdapter unit tests."""

import prometheus_client
import pytest
from flask.testing import FlaskClient

from src.api.http_adapter import HttpApiAdapter
from src.offers.offer_service import OfferService
from tests.unit.test_doubles import (
    ConfigRepoStub,
    MetadataServiceStub,
    OfferServiceSpy,
)


@pytest.fixture()
def offer_service_spy() -> OfferServiceSpy:
    """Fresh OfferServiceSpy per test."""
    return OfferServiceSpy()


@pytest.fixture()
def http_client(offer_service_spy: OfferService) -> FlaskClient:
    """Flask test client wired with stub dependencies.

    Args:
        offer_service_spy: Spy injected so tests can assert on recorded calls.

    Returns:
        A Flask test client.
    """
    return setup_http_client(offer_service_spy)


def setup_http_client(offer_service: OfferService) -> FlaskClient:
    """Setup a Flask test client with the given OfferService."""
    prometheus_client.REGISTRY = prometheus_client.CollectorRegistry(auto_describe=True)
    adapter = HttpApiAdapter(
        config=ConfigRepoStub(),
        metadata_service=MetadataServiceStub(),
        offer_service=offer_service,
    )
    adapter.flask_app.config.update({"TESTING": True})  # pyright: ignore[reportUnknownMemberType] We lack type stubs for Flask config
    return adapter.flask_app.test_client()
