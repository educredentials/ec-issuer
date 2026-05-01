# End-to-End Testing

This document describes end-to-end testing for the EC Issuer service.

## Overview

End-to-end tests verify the complete system behavior by making real HTTP requests to the running service. The `just test-e2e` command uses Podman Compose to start the required service containers.

## Prerequisites

- Podman installed and running
- Docker Compose compatible with podman-compose

## Running Tests

```bash
just test-e2e
```

The `just test-e2e` command starts all services defined in `compose.yaml` and waits for them to be healthy before running tests.

**Note:** Test fixtures themselves never start or stop services. They only return connection strings. If services are not running when tests execute, they will fail with clear connection errors (KISS principle).

## Schema Validation

We use the `jsonschema` library to validate JSON responses against schemas defined in the `tests/e2e/schemas/` directory. The `assert_schema()` helper function in `tests/e2e/conftest.py` handles the validation:

```python
from tests.e2e.conftest import assert_schema

response = e2e_client.get("/.well-known/openid-credential-issuer")
body = response.json()
assert_schema(body, "credential_issuer_metadata")
```

This validates that `body` matches the schema defined in `tests/e2e/schemas/credential_issuer_metadata.json`.

## Generating Schemas from Dataclasses

When the schema needs to match a Python dataclass (like `CredentialIssuerMetadata`), you can [use msgspec to generate it automatically](https://jcristharif.com/msgspec/jsonschema.html). This ensures the schema stays in sync with the dataclass definition. 

### Example: Generating a Schema for CredentialIssuerMetadata

```python
import msgspec
from src.metadata.metadata import CredentialIssuerMetadata

# Generate the schema
schema = msgspec.json.schema(CredentialIssuerMetadata)

# Write to file
with open("tests/e2e/schemas/credential_issuer_metadata.json", "w") as f:
    f.write(msgspec.json.encode(schema).decode())
```

This generates a complete schema with:
- All required and optional fields from the dataclass
- Proper type definitions
- Nested type references using `$ref` and `$defs`
- Nullable types handled correctly (`anyOf` with `null`)

### Example Output

The generated schema for `CredentialIssuerMetadata` includes:

```json
{
  "$ref": "#/$defs/CredentialIssuerMetadata",
  "$defs": {
    "CredentialIssuerMetadata": {
      "title": "CredentialIssuerMetadata",
      "type": "object",
      "properties": {
        "credential_issuer": {"type": "string"},
        "credential_endpoint": {"type": "string"},
        "credential_configurations_supported": {
          "type": "object",
          "additionalProperties": {"$ref": "#/$defs/CredentialConfiguration"}
        },
        "authorization_servers": {
          "anyOf": [
            {"type": "array", "items": {"type": "string"}},
            {"type": "null"}
          ],
          "default": null
        },
        ...
      },
      "required": ["credential_issuer", "credential_endpoint", "credential_configurations_supported"]
    },
    ...
  }
}
```

## When to Update Schemas

Update schemas when:
- The dataclass definition changes (fields added/removed/renamed)
- The API response structure changes
- You add new endpoints that return JSON

To update a schema:

1. Run the msgspec schema generation command
2. Review the generated schema
3. Save it to the appropriate file in `tests/e2e/schemas/`

## Benefits

- **Type Safety**: Schemas validate the exact structure of responses
- **Maintainability**: Generated schemas stay in sync with dataclasses
- **Documentation**: Schemas serve as documentation for API responses
- **Early Failure**: Tests fail fast if the response structure is wrong
