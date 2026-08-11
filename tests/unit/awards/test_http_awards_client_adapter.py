"""Unit tests for HttpAwardsClientAdapter."""

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
    _ob3_default_schema,  # pyright:ignore[reportPrivateUsage]
)
from src.lib.http_client import HttpClient

from ..support.requests_doubles import MockResponse, RequestsSpy

_BADGR_AWARD_JSON = (
    b'{"id":32,"entity_id":"http://example.com/'
    b'awards/3527","name":"Teamwork Badge",'
    b'"issued_on":"2010-01-01T00:00:00Z",'
    b'"badgr":null,"revoked":false,"public":true,'
    b'"grade_achieved":null,"expires_at":null,'
    b'"badgeclass":{"id":18,"name":"Teamwork Badge",'
    b'"entity_id":"http://example.com/'
    b'badgeclasses/21",'
    b'"description":"Demonstrates the ability to work effectively",'
    b'"criteria_text":"Successfully complete the teamwork project",'
    b'"issuer":{'
    b'"name_dutch":null,"name_english":null,'
    b'"faculty":null}}}'
)

_EXPECTED_BADGR_AWARD = Award(
    id="http://example.com/awards/3527",
    type=["VerifiableCredential", "AchievementCredential"],
    name="Teamwork Badge",
    issuer=Issuer(
        id="",
        type=["Profile"],
        name="Teamwork Badge",
    ),
    validFrom="2010-01-01T00:00:00Z",
    credentialSubject=AchievementSubject(
        id="http://example.com/awards/3527",
        type=["AchievementSubject"],
        achievement=Achievement(
            id="http://example.com/awards/3527",
            type=["Achievement"],
            criteria=Criteria(
                narrative="Successfully complete the teamwork project",
            ),
            description=("Demonstrates the ability to work effectively"),
            name="Teamwork Badge",
        ),
    ),
    credentialSchema=_ob3_default_schema(),
)


@pytest.fixture
def http_client() -> RequestsSpy:
    """Provide a fresh RequestsSpy for each test."""
    return RequestsSpy()


@pytest.fixture
def subject(http_client: HttpClient) -> HttpAwardsClientAdapter:
    """Provide the adapter wired to the spy."""
    return HttpAwardsClientAdapter(
        awards_service_url="http://awards.example.com/awards/", http_client=http_client
    )


@pytest.fixture
def valid_badgr_award_response() -> MockResponse:
    """Provide a 200 response with Badgr award JSON."""
    return MockResponse(status_code=200, _content=_BADGR_AWARD_JSON)


class TestHttpAwardsClientAdapter:
    """Tests for the HttpAwardsClientAdapter class."""

    def test_get_sends_get_to_correct_url(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
        valid_badgr_award_response: MockResponse,
    ) -> None:
        """get() sends a GET request to /awards/{award_id}."""
        http_client.set_response(valid_badgr_award_response)
        _ = subject.get("award-123", "fake_token")
        call = http_client.calls[0]
        assert call.method == "get"
        assert call.url == "http://awards.example.com/awards/award-123"
        assert call.headers == {"Authorization": "Bearer fake_token"}

    def test_get_returns_award_from_response(
        self,
        http_client: RequestsSpy,
        subject: HttpAwardsClientAdapter,
        valid_badgr_award_response: MockResponse,
    ) -> None:
        """get() decodes and returns the Award from a 200 response."""
        http_client.set_response(valid_badgr_award_response)
        result = subject.get("award-123", "fake_token")
        assert result == _EXPECTED_BADGR_AWARD

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
            _ = subject.get("award-999", "fake_token")

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
            _ = subject.get("award-123", "fake_token")

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
            _ = subject.get("award-123", "fake_token")

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
            _ = subject.get("award-123", "fake_token")

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
            _ = subject.get("award-123", "fake_token")
