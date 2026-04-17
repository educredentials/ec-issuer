import os

import pytest
from requests import request

class Config:
    public_url: str = os.environ["PUBLIC_URL"]


class HttpClient:
    _service_url: str

    def __init__(self, config: Config):
        self._service_url = config.public_url

    def get(self, path: str):
        return self._request("GET", path)

    def post(
        self, path: str, json: dict[str, str], headers: dict[str, str] | None = None
    ):
        return self._request("POST", path, json=json, headers=headers)

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ):
        url = f"{self._service_url}/{path}"
        return request(method, url, json=json, headers=headers)


@pytest.fixture(scope="session")
def config() -> Config:
    return Config()


@pytest.fixture(scope="session")
def e2e_client(config: Config) -> HttpClient:
    """Create a generic HTTP client with request"""
    return HttpClient(config)
