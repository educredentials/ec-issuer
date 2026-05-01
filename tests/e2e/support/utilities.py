"""Utility functions for e2e tests."""

import json
from pathlib import Path

from jsonpath_ng import (  # pyright: ignore[reportMissingTypeStubs]
    parse as jsonpath_parse,  # pyright: ignore[reportUnknownVariableType]
)

_TESTS_E2E_DIR = Path(__file__).parent.parent
_SCHEMAS_DIR = _TESTS_E2E_DIR / "schemas"


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
    import jsonschema

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
