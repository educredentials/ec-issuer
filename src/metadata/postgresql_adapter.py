"""PostgreSQL adapter for the metadata repository."""

from typing import cast, override

import msgspec
import psycopg2
from psycopg2.extensions import connection as _connection

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import (
    MetadataNotFoundError,
    MetadataSerializationError,
)
from src.metadata.metadata_repository import MetadataRepositoryPort


class PostgreSQLMetadataRepository(MetadataRepositoryPort):
    """Adapter that stores metadata in a PostgreSQL database."""

    _conn: _connection
    _connection_string: str

    def __init__(self, connection_string: str) -> None:
        """Initialise with a PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string.
        """
        self._connection_string = connection_string
        self._conn = psycopg2.connect(connection_string)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database table for issuer metadata."""
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS issuer_metadata (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    metadata JSONB NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_issuer_metadata_created_at
                ON issuer_metadata (created_at)
                """
            )
            self._conn.commit()

    def clear_db(self) -> None:
        """Clear all metadata from the database table."""
        with self._conn.cursor() as cursor:
            cursor.execute("DELETE FROM issuer_metadata")
            self._conn.commit()

    def close_db(self) -> None:
        """Close the database connection."""
        self._conn.close()

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

        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO issuer_metadata (metadata)
                VALUES (%s)
                """,
                (metadata_json,),
            )
            self._conn.commit()

    @override
    def get(self) -> CredentialIssuerMetadata:
        """Retrieve the latest metadata entry by created_at.

        Returns:
            The latest CredentialIssuerMetadata.

        Raises:
            MetadataNotFoundError: When no metadata entry exists.
            MetadataSerializationError: When metadata cannot be deserialized.
        """
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT metadata
                FROM issuer_metadata
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
        self._conn.commit()

        if row is None:
            raise MetadataNotFoundError("No metadata entry found")

        # psycopg2 returns JSONB as a dict, encode to bytes for msgspec
        metadata_dict = cast(dict[str, object], row[0])
        try:
            metadata_json = msgspec.json.encode(metadata_dict)
            return msgspec.json.decode(metadata_json, type=CredentialIssuerMetadata)
        except msgspec.DecodeError as exc:
            raise MetadataSerializationError(
                f"Failed to deserialize metadata: {exc}"
            ) from exc
