"""PostgreSQL adapter for the metadata repository."""

from typing import cast, override

import msgspec

from src.lib.postgresql_base import PostgreSQLRepositoryBase
from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import (
    MetadataNotFoundError,
    MetadataRepositoryPort,
    MetadataSerializationError,
)


class PostgreSQLMetadataRepository(PostgreSQLRepositoryBase, MetadataRepositoryPort):
    """Adapter that stores metadata in a PostgreSQL database."""

    def __init__(self, connection_string: str) -> None:
        """Initialise with a PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string.
        """
        PostgreSQLRepositoryBase.__init__(self, connection_string)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database table for issuer metadata."""
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS issuer_metadata (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                metadata JSONB NOT NULL
            )
            """
        )
        self.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_issuer_metadata_created_at
            ON issuer_metadata (created_at)
            """
        )

    def clear_db(self) -> None:
        """Clear all metadata from the database table."""
        self.execute("DELETE FROM issuer_metadata")

    @override
    def store(self, metadata: CredentialIssuerMetadata) -> None:
        """Persist metadata in PostgreSQL.

        Args:
            metadata: The CredentialIssuerMetadata to store.

        Raises:
            MetadataSerializationError: When metadata cannot be serialized.
        """
        try:
            metadata_json = msgspec.json.encode(metadata).decode("utf-8")
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            raise MetadataSerializationError(
                f"Failed to serialize metadata: {exc}"
            ) from exc

        self.execute(
            "INSERT INTO issuer_metadata (metadata) VALUES (%s)",
            (metadata_json,),
        )

    @override
    def get(self) -> CredentialIssuerMetadata:
        """Retrieve the latest metadata entry by created_at.

        Returns:
            The latest CredentialIssuerMetadata.

        Raises:
            MetadataNotFoundError: When no metadata entry exists.
            MetadataSerializationError: When metadata cannot be deserialized.
        """
        with self.conn() as conn:
          row = conn.cursor().execute(
            """
            SELECT metadata
            FROM issuer_metadata
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            raise MetadataNotFoundError("No metadata entry found")

        # psycopg returns JSONB as a dict, encode to bytes for msgspec
        metadata_dict = cast(dict[str, object], row[0])
        try:
            metadata_json = msgspec.json.encode(metadata_dict)
            return msgspec.json.decode(metadata_json, type=CredentialIssuerMetadata)
        except msgspec.DecodeError as exc:
            raise MetadataSerializationError(
                f"Failed to deserialize metadata: {exc}"
            ) from exc
