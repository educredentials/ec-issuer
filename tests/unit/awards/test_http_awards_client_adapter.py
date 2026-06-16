"""Unit tests for HttpAwardsClientAdapter."""

import msgspec
import pytest

from src.awards.awards_client_port import (
    AwardForbidden,
    AwardNotFound,
    AwardsClientError,
)
from src.awards.http_awards_client_adapter import HttpAwardsClientAdapter
from src.awards.models import (
    Achievement,
    AchievementSubject,
    Award,
    Criteria,
    Issuer,
)
from src.lib.http_client import HttpClient

from ..support.requests_doubles import MockResponse, RecordedRequest, RequestsSpy

_VALID_AWARD_JSON = msgspec.json.encode(
    {
        "id": "http://example.com/credentials/3527",
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "name": "Teamwork Badge",
        "issuer": {
            "id": "https://example.com/issuers/876543",
            "type": ["Profile"],
            "name": "Example Corp",
        },
        "validFrom": "2010-01-01T00:00:00Z",
        "credentialSubject": {
            "id": "did:example:ebfeb1f712ebc6f1c276e12ec21",
            "type": ["AchievementSubject"],
            "achievement": {
                "id": "https://example.com/achievements/21st-century-skills/teamwork",
                "type": ["Achievement"],
                "criteria": {
                    "narrative": (
                        "Team members are nominated for this badge by their peers."
                    )
                },
                "description": (
                    "This badge recognizes the capacity to collaborate in a group."
                ),
                "name": "Teamwork",
            },
        },
    }
)

_EXPECTED_AWARD = Award(
    id="http://example.com/credentials/3527",
    type=["VerifiableCredential", "OpenBadgeCredential"],
    name="Teamwork Badge",
    issuer=Issuer(
        id="https://example.com/issuers/876543",
        type=["Profile"],
        name="Example Corp",
    ),
    validFrom="2010-01-01T00:00:00Z",
    credentialSubject=AchievementSubject(
        id="did:example:ebfeb1f712ebc6f1c276e12ec21",
        type=["AchievementSubject"],
        achievement=Achievement(
            id="https://example.com/achievements/21st-century-skills/teamwork",
            type=["Achievement"],
            criteria=Criteria(
                narrative="Team members are nominated for this badge by their peers."
            ),
            description="This badge recognizes the capacity to collaborate in a group.",
            name="Teamwork",
        ),
    ),
)


@pytest.fixture
def http_client() -> RequestsSpy:
    """Provide a fresh RequestsSpy for each test."""
    return RequestsSpy()


@pytest.fixture
def subject(http_client: HttpClient) -> HttpAwardsClientAdapter:
    """Provide the adapter wired to the spy."""
    return HttpAwardsClientAdapter(
        awards_service_url="http://awards.example.com", http_client=http_client
    )


@pytest.fixture
def valid_award_response() -> MockResponse:
    """Provide a 200 response with valid award JSON."""
    return MockResponse(status_code=200, _content=_VALID_AWARD_JSON)


class TestHttpAwardsClientAdapter:
    """Tests for the HttpAwardsClientAdapter class."""

    def test_get_sends_get_to_correct_url(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
        valid_award_response: MockResponse,
    ) -> None:
        """get() sends a GET request to /awards/{award_id}."""
        http_client.set_response(valid_award_response)
        _ = subject.get("award-123")
        assert http_client.calls[0] == RecordedRequest(
            method="get",
            url="http://awards.example.com/awards/award-123",
        )

    def test_get_returns_award_from_response(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
        valid_award_response: MockResponse,
    ) -> None:
        """get() decodes and returns the Award from a 200 response."""
        http_client.set_response(valid_award_response)
        result = subject.get("award-123")
        assert result == _EXPECTED_AWARD

    def test_get_raises_award_not_found_on_404(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
    ) -> None:
        """get() raises AwardNotFound when the service returns 404."""
        http_client.set_response(
            MockResponse(status_code=404, _content=b'{"error": "Award not found"}')
        )
        with pytest.raises(AwardNotFound):
            _ = subject.get("award-999")

    def test_get_raises_award_forbidden_on_403(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
    ) -> None:
        """get() raises AwardForbidden when the service returns 403."""
        http_client.set_response(
            MockResponse(status_code=403, _content=b'{"error": "Forbidden"}')
        )
        with pytest.raises(AwardForbidden):
            _ = subject.get("award-123")

    def test_get_raises_awards_client_error_on_500(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
    ) -> None:
        """get() raises AwardsClientError when the service returns a 5xx error."""
        http_client.set_response(
            MockResponse(status_code=500, _content=b'"Internal Server Error"')
        )
        with pytest.raises(AwardsClientError):
            _ = subject.get("award-123")

    def test_get_raises_awards_client_error_on_4xx(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
    ) -> None:
        """get() raises AwardsClientError on unexpected 4xx (not 403 or 404)."""
        http_client.set_response(
            MockResponse(status_code=422, _content=b'"Unprocessable"')
        )
        with pytest.raises(AwardsClientError):
            _ = subject.get("award-123")

    def test_get_raises_awards_client_error_on_invalid_json(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
    ) -> None:
        """get() raises AwardsClientError when the response is not valid JSON."""
        http_client.set_response(
            MockResponse(status_code=200, _content=b"not valid json")
        )
        with pytest.raises(AwardsClientError):
            _ = subject.get("award-123")
