"""Credential template bootstrap logic.

Resolves credential template IDs by reading JSON files, parsing them
with msgspec into CredentialTemplate, deriving the credential type from
the ``dataModel`` field, and delegating to the service to find or
create each template on the SSI Agent.
"""

import os
from pathlib import Path

import msgspec

from src.credential_configurations import (
    ssi_agent_credential_configurations_client_adapter as ssi_cred_client,
)
from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateClientError,
)
from src.credential_configurations.credential_configurations_service import (
    CredentialTemplateService,
)
from src.credential_configurations.models import CredentialTemplate
from src.offers.models import CredentialType, is_known_credential_type


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


def resolve_credential_template_ids(
    json_dir: str | None = None,
) -> dict[CredentialType, str]:
    """Resolve credential template IDs from a directory of JSON files.

    Each template's credential type is derived from its ``dataModel`` field
    (``open_badges_3-0`` → OB3, ``european_learning_model_v3-3`` → EDC).
    Fails fast if either type is missing, duplicated, or unrecognised.

    Args:
        json_dir: Path to the directory containing template JSON files.
            Falls back to ``CREDENTIAL_TEMPLATE_JSON_DIR`` env var.

    Returns:
        A dict mapping ``CredentialType.OB3`` and ``CredentialType.EDC``
        to their resolved template IDs.

    Raises:
        RuntimeError: If the directory is missing/empty, contains
            invalid/unrecognised templates, or the SSI Agent is unreachable.
    """
    if json_dir is None:
        json_dir = (os.environ.get("CREDENTIAL_TEMPLATE_JSON_DIR", "")).strip()

    if not json_dir:
        raise RuntimeError(
            "Credential template directory not configured. "
            + "Set CREDENTIAL_TEMPLATE_JSON_DIR."
        )

    return load_from_directory(json_dir)


def load_from_directory(
    json_dir: str,
) -> dict[CredentialType, str]:
    """Load credential templates from a directory, keyed by type.

    Parses each .json file, derives its credential type from the
    ``dataModel`` field, registers it on the SSI Agent, and returns
    a dict of ``CredentialType -> template_id``.

    Args:
        json_dir: Path to the directory containing .json template files.

    Returns:
        A dict mapping each resolved ``CredentialType`` to its template ID.

    Raises:
        RuntimeError: If the directory is missing, empty, contains
            invalid templates, duplicates, or unknown types, or the
            SSI Agent is unreachable.
    """
    dir_path = Path(json_dir)

    if not dir_path.is_dir():
        raise RuntimeError(f"Credential template directory not found: {json_dir}")

    json_files = sorted(
        f for f in dir_path.iterdir() if f.suffix == ".json" and f.is_file()
    )

    if not json_files:
        raise RuntimeError(
            f"No .json files found in credential template directory: {json_dir}"
        )

    ssi_agent_url = os.environ.get("SSI_AGENT_URL", "")
    client = ssi_cred_client.SsiAgentCredentialTemplateClientAdapter(
        ssi_agent_url=ssi_agent_url,
    )
    service = CredentialTemplateService(client=client)

    template_ids: dict[CredentialType, str] = {}

    for json_file in json_files:
        try:
            json_str = json_file.read_text(encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(
                f"Could not read credential template file: {json_file}"
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

        # Derive credential type from dataModel field.
        if template.dataModel is None:
            raise RuntimeError(
                f"Credential template {json_file} is missing a 'dataModel' field."
            )
        try:
            cred_type: CredentialType = is_known_credential_type(template.dataModel)
        except ValueError as exc:
            raise RuntimeError(
                f"Unrecognised dataModel in {json_file}: {template.dataModel}. "
                + "Expected 'open_badges_3-0' or 'european_learning_model_v3-3'."
            ) from exc

        if cred_type in template_ids:
            raise RuntimeError(
                f"Duplicate credential type {cred_type.value} in {json_file}. "
                + f"Already resolved from {template_ids[cred_type]}"
            )

        try:
            created = service.ensure_by_title(template, ssi_agent_url=ssi_agent_url)
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
                "SSI Agent returned a credential template with no ID "
                + f"(file: {json_file}). This indicates an upstream issue."
            )

        template_ids[cred_type] = created.id

    # Fail fast: both types are required.
    for required_type in CredentialType:
        if required_type not in template_ids:
            raise RuntimeError(
                f"Missing credential template for type {required_type.value} "
                + f"in directory: {json_dir}"
            )

    return template_ids


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
        raise RuntimeError(f"Credential template file not found: {json_file}") from exc

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
        created = service.ensure_by_title(template, ssi_agent_url=ssi_agent_url)
    except RuntimeError as exc:
        if "Failed to reach SSI Agent" in str(exc):
            raise
        raise
    except CredentialTemplateClientError as exc:
        raise RuntimeError(f"Failed to reach SSI Agent {ssi_agent_url}: {exc}") from exc

    if not created.id:
        raise RuntimeError(
            "SSI Agent returned a credential template with no ID. "
            + "This indicates an upstream issue."
        )

    return created.id
