"""Test doubles for the requests library.

This module provides spy implementations that mimic the python requests module
for use in unit tests.

It should normally not be used in integration tests, but if there's a solid use
case to re-use it there, move this to a common lib.
It should definitely not be used in e2e tests.
"""

from dataclasses import dataclass, field

from typing_extensions import override

from src.lib.http_client import JSON, HttpResponse


@dataclass
class MockResponse(HttpResponse):
    """Mock Response object that mimics requests.Response."""

    _content: bytes = field(default_factory=bytes)
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    url: str = ""
    ok: bool = True
    reason: str = "OK"

    @property
    @override
    def content(self) -> bytes:
        return self._content

    @property
    @override
    def text(self) -> str:
        return self._content.decode()

    @property
    @override
    def json(self) -> dict[str, object]:
        """Return parsed JSON content.

        Returns:
            The parsed JSON data from content.
        """
        import msgspec

        return msgspec.json.decode(self.content) if self.content else {}


@dataclass
class RecordedRequest:
    """Record of a single HTTP request."""

    method: str
    url: str
    json: object | None = None


class RequestsSpy:
    """Spy that records all calls made to HTTP methods.

    This class mimics the requests module interface and records all calls
    to get, post, put, delete methods along with their arguments.
    """

    _calls: list[RecordedRequest]
    _next_response: MockResponse | None

    def __init__(self) -> None:
        """Initialize with empty call log."""
        self._calls = []
        self._next_response = None

    @property
    def calls(self) -> list[RecordedRequest]:
        """Return all calls made to this spy.

        Returns:
            A list of recorded request objects.
        """
        return self._calls

    def get(self, url: str) -> MockResponse:
        """Record a GET request and return a mock response.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments passed to requests.get().

        Returns:
            A mock Response object.
        """
        self._calls.append(RecordedRequest(method="get", url=url, json=None))
        return self._next_response_or_default(url)

    def post(
        self,
        url: str,
        json: JSON,  # pyright: ignore[reportExplicitAny, reportAny]
    ) -> MockResponse:
        """Record a POST request and return a mock response.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments passed to requests.post().

        Returns:
            A mock Response object.
        """
        self._calls.append(RecordedRequest(method="post", url=url, json=json))  # pyright: ignore[reportAny]
        return self._next_response_or_default(url=url)

    def put(
        self,
        url: str,
        json: object,
    ) -> MockResponse:
        """Record a PUT request and return a mock response.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments passed to requests.put().

        Returns:
            A mock Response object.
        """
        self._calls.append(RecordedRequest(method="put", url=url, json=json))
        return self._next_response_or_default(url=url)

    def delete(self, url: str, json: object | None = None) -> MockResponse:
        """Record a DELETE request and return a mock response.

        Args:
            url: The URL to request.
            **kwargs: Additional arguments passed to requests.delete().

        Returns:
            A mock Response object.
        """
        self._calls.append(RecordedRequest(method="delete", url=url, json=json))
        return self._next_response_or_default(url=url)

    def set_response(self, response: MockResponse) -> None:
        """Set the response to be returned by the next request.

        Args:
            response: The response to return.
        """
        self._next_response = response

    def _next_response_or_default(self, url: str) -> MockResponse:
        """Return the next response or a default response if none is set."""
        if self._next_response is None:
            return MockResponse(url=url)
        else:
            response = self._next_response
            self._next_response = None
            return response


# Module-level instance for convenient import
requests = RequestsSpy()
