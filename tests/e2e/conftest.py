import json
import os
from pathlib import Path

import jsonschema
import pytest
from jsonpath_ng import parse as jsonpath_parse  # pyright: ignore[reportMissingTypeStubs,reportUnknownVariableType]
from requests import request

_SCHEMAS_DIR = Path(__file__).parent / "schemas"


def load_schema(schema_name: str) -> dict[str, object]:
    """Load a JSON schema file from the schemas directory.

    Args:
        schema_name: Filename without extension, e.g. "credential_offer".

    Returns:
        The parsed schema as a dictionary.
    """
    return json.loads(  # pyright: ignore[reportAny]
        (_SCHEMAS_DIR / f"{schema_name}.json").read_text()
    )


def assert_schema(data: object, schema_name: str) -> None:
    """Validate data against a JSON schema file in the schemas directory.

    Args:
        data: The parsed JSON data to validate.
        schema_name: Filename without extension, e.g. "credential_offer".

    Raises:
        jsonschema.ValidationError: When data does not match the schema.
    """
    jsonschema.validate(data, load_schema(schema_name))


def jsonpath_value(data: object, expression: str) -> object:
    """Extract a single value from data using a JSONPath expression.

    Args:
        data: The parsed JSON data to search.
        expression: A JSONPath expression, e.g. "$.grants.issuer_state".

    Returns:
        The first matched value.

    Raises:
        IndexError: When the expression matches nothing.
    """
    matches = jsonpath_parse(expression).find(data)  # pyright: ignore[reportUnknownMemberType]
    return matches[0].value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]


class Config:
    """E2E test configuration loaded from environment variables."""

    public_url: str = os.environ["PUBLIC_URL"]


class HttpClient:
    """Thin HTTP client for e2e tests."""

    _service_url: str

    def __init__(self, config: Config):
        """Initialise with service base URL from config.

        Args:
            config: Test configuration.
        """
        self._service_url = config.public_url

    def get(self, path: str):
        """Send a GET request to the service.

        Args:
            path: URL path relative to the service base URL.
        """
        return self._request("GET", path)

    def post(
        self, path: str, json: dict[str, str], headers: dict[str, str] | None = None
    ):
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
        json: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ):
        url = f"{self._service_url}/{path}"
        return request(method, url, json=json, headers=headers)


@pytest.fixture(scope="session")
def config() -> Config:
    """Provide test configuration."""
    return Config()


@pytest.fixture(scope="session")
def e2e_client(config: Config) -> HttpClient:
    """Provide a generic HTTP client pointed at the service under test."""
    return HttpClient(config)
