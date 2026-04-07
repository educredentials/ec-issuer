import os

import pytest
from requests import request


class TestClient:
    server_host: str = os.environ["SERVER_HOST"]
    server_port: int = int(os.environ["SERVER_PORT"])

    def get(self, path: str):
        return self._request("GET", path)

    def _request(self, method: str, path: str):
        url = f"http://{self.server_host}:{self.server_port}/{path}"
        return request(method, url)


@pytest.fixture(scope="session")
def e2e_client() -> TestClient:
    """Create a generic HTTP client with request"""
    return TestClient()
