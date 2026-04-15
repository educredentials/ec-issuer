import os

import pytest
from requests import request


class TestClient:
    server_host: str = os.environ["SERVER_HOST"]
    server_port: int = int(os.environ["SERVER_PORT"])

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
        url = f"http://{self.server_host}:{self.server_port}/{path}"
        return request(method, url, json=json, headers=headers)


@pytest.fixture(scope="session")
def e2e_client() -> TestClient:
    """Create a generic HTTP client with request"""
    return TestClient()
