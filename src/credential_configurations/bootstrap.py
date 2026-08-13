"""Credential template bootstrap logic.

Resolves a credential template ID by reading a JSON file,
parsing it with msgspec into a CredentialTemplate, and
delegating to the service to find or create it on the SSI Agent.
"""

import os

import msgspec

from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateClientError,
)
from src.credential_configurations.credential_configurations_service import (
    CredentialTemplateService,
)
from src.credential_configurations.models import CredentialTemplate
from src.credential_configurations import (
    ssi_agent_credential_configurations_client_adapter as ssi_cred_client,
)


def resolve_credential_template_id() -> str:
    """Resolve credential template ID via JSON file or env var.

    Priority:
    1. CREDENTIAL_TEMPLATE_JSON_FILE -> parse JSON, ensure template on SSI Agent
    2. CREDENTIAL_TEMPLATE_ID -> return env var value directly

    The JSON file is parsed with msgspec into a CredentialTemplate dataclass.
    Nested fields (display/logo) are decoded automatically by msgspec.

    Returns:
        The resolved credential template ID.

    Raises:
        RuntimeError: If JSON file is missing/invalid, has no title,
            the SSI Agent is unreachable, or no template ID is configured.
    """
    json_file = os.environ.get("CREDENTIAL_TEMPLATE_JSON_FILE", "").strip()
    if json_file:
        return load_from_json(json_file)

    template_id = os.environ.get("CREDENTIAL_TEMPLATE_ID", "").strip()
    if template_id:
        return template_id

    raise RuntimeError(
        "No credential configuration ID configured. "
        + "Set CREDENTIAL_TEMPLATE_JSON_FILE or CREDENTIAL_TEMPLATE_ID."
    )


def load_from_json(json_file: str) -> str:
    """Parse credential template JSON and ensure it exists on SSI Agent.

    Args:
        json_file: Path to the JSON template file.

    Returns:
        The ID of the credential template on the SSI Agent.

    Raises:
        RuntimeError: If the file is missing, invalid, has no title,
            or the SSI Agent is unreachable or creation fails.
    """
    try:
        json_str = open(json_file).read()  # noqa: SIM115
    except Exception as exc:
        raise RuntimeError(
            f"Credential template file not found: {json_file}"
        ) from exc

    try:
        template: CredentialTemplate = msgspec.json.decode(
            json_str, type=CredentialTemplate
        )
    except msgspec.DecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in credential template file {json_file}: {exc}"
        ) from exc

    if not template.title or not template.title.strip():
        raise RuntimeError(
            "Credential template JSON is missing a non-empty 'title' field "
            + f"(file: {json_file})."
        )

    ssi_agent_url = os.environ["SSI_AGENT_URL"]
    client = ssi_cred_client.SsiAgentCredentialTemplateClientAdapter(
        ssi_agent_url=ssi_agent_url,
    )
    service = CredentialTemplateService(client=client)

    try:
        created = service.ensure_by_title(
            template, ssi_agent_url=ssi_agent_url
        )
    except RuntimeError as exc:
        if "Failed to reach SSI Agent" in str(exc):
            raise
        raise
    except CredentialTemplateClientError as exc:
        raise RuntimeError(
            f"Failed to reach SSI Agent {ssi_agent_url}: {exc}"
        ) from exc

    if not created.id:
        raise RuntimeError(
            "SSI Agent returned a credential template with no ID. "
            + "This indicates an upstream issue."
        )

    return created.id
