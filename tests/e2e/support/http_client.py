"""HTTP client for e2e tests."""

import os
from dataclasses import dataclass

from requests import request
from requests.models import Response


@dataclass
class Config:
    """E2E test configuration loaded from environment variables."""

    public_url: str = os.environ["PUBLIC_URL"]
    ssi_agent_url: str = os.environ["SSI_AGENT_URL"]


class HttpClient:
    """Thin HTTP client for e2e tests."""

    _service_url: str
    _default_headers: dict[str, str] = {}

    def __init__(self, config: Config):
        """Initialise with service base URL from config.

        Args:
            config: Test configuration.
        """
        self._service_url = config.public_url
        self._default_headers = {}

    def get(self, path: str, headers: dict[str, str] | None = None) -> Response:
        """Send a GET request to the service.

        Args:
            path: URL path relative to the service base URL.
            headers: Optional HTTP headers.
        """
        return self._request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Send a POST request to the service.

        Args:
            path: URL path relative to the service base URL.
            json: Request body as a dict, serialised to JSON.
            headers: Optional HTTP headers.
        """
        return self._request("POST", path, json=json, headers=headers)

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        if path.startswith('http://') or path.startswith('https://'): # Absolute
            url = path
        else:
            url = f"{self._service_url}/{path}"

        combined_headers = {**self._default_headers, **(headers or {})}
        return request(method, url, json=json, headers=combined_headers)
