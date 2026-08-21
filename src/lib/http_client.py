"""HTTP client interface for dependency injection."""
# BK: Ignored, because this is how "requests" works, and wrapping it to avoid
# typing issues adds far too much complexity.
# pyright: reportExplicitAny=false, reportAny=false

from typing import Any, Protocol, TypeAlias

import requests


# any object that can be serialized to JSON. Used exactly like this in requests
JSON: TypeAlias = Any


class HttpResponse(Protocol):
    """Protocol defining the HTTP response interface.

    This protocol allows type-safe access to response objects from both
    real HTTP clients and test doubles.
    """

    status_code: int
    url: str

    @property
    def json(self) -> JSON:
        """Return the JSON response content."""
        ...

    @property
    def content(self) -> bytes:
        """Return the raw response content."""
        ...

    @property
    def text(self) -> str:
        """Return the response content as a string."""
        ...


class HttpClient(Protocol):
    """Protocol defining the HTTP client interface.

    This protocol allows dependency injection of HTTP clients for testing
    while maintaining type safety and following the project's architectural patterns.

    The protocol is designed to be compatible with both the requests module
    and test doubles that implement the same interface.
    """

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        """Send a GET request.

        Args:
            url: The URL to request.
            headers: Optional HTTP headers.

        Returns:
            The response object.
        """
        ...

    def post(self, url: str, json: JSON) -> HttpResponse:
        """Send a POST request.

        Args:
            url: The URL to request.
            **kwargs: Additional request parameters.

        Returns:
            The response object.
        """
        ...

    def put(self, url: str, json: JSON) -> HttpResponse:
        """Send a PUT request.

        Args:
            url: The URL to request.
            **kwargs: Additional request parameters.

        Returns:
            The response object.
        """
        ...

    def delete(self, url: str, json: JSON | None = None) -> HttpResponse:
        """Send a DELETE request.

        Args:
            url: The URL to request.
            **kwargs: Additional request parameters.

        Returns:
            The response object.
        """
        ...


class RequestsHttpClient:
    """Adapter that makes the requests module compatible with HttpClient protocol.

    This is a simple wrapper that delegates to the requests module functions.
    While the requests module itself could potentially be used directly,
    this wrapper ensures explicit compatibility with the HttpClient protocol.
    """

    _default_timeout: int = 10

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        return self._request("GET", url, headers=headers)

    def post(self, url: str, json: JSON) -> HttpResponse:
        return self._request("POST", url, json=json)

    def put(self, url: str, json: JSON) -> HttpResponse:
        return self._request("PUT", url, json=json)

    def delete(self, url: str, json: JSON | None = None) -> HttpResponse:
        return self._request("DELETE", url, json=json)

    def _request(
        self,
        method: str,
        url: str,
        json: JSON | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        kwargs: dict[str, object] = {"timeout": self._default_timeout}
        if json is not None:
            kwargs["json"] = json
        if headers is not None:
            kwargs["headers"] = headers
        return requests.request(
            method=method,
            url=url,
            **kwargs,
        )
