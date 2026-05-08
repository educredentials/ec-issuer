"""Command-line adapter for sysadmin operations."""

import os
import sys

import msgspec

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.postgresql_adapter import PostgreSQLMetadataRepository

from .sysadmin_service import SysadminService

_USAGE = """\
Usage: ec-issuer-cli <command> [args]

Commands:
  update-issuer-metadata   Store credential issuer metadata JSON from stdin.

Examples:
  Update metadata from a json file on disk
  ec-issuer-cli update-issuer-metadata < ~/metadata_example.json
"""


def _build_service() -> SysadminService:
    connection_string = os.environ["POSTGRES_CONNECTION_STRING"]
    metadata_repository = PostgreSQLMetadataRepository(connection_string)
    return SysadminService(metadata_repository=metadata_repository)


def _cmd_update_issuer_metadata() -> None:
    content = sys.stdin.read()
    try:
        metadata = msgspec.json.decode(content, type=CredentialIssuerMetadata)
    except msgspec.DecodeError as e:
        print(f"Error: invalid metadata JSON: {e}", file=sys.stderr)
        sys.exit(1)

    _build_service().update_credential_issuer_metadata(metadata)
    print("Credential issuer metadata updated.")


def main() -> None:
    """Entry point for the ec-issuer-cli command."""
    match sys.argv[1:]:
        case ["update-issuer-metadata"]:
            _cmd_update_issuer_metadata()
        case _:
            print(_USAGE, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
