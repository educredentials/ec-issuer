"""Integration tests for PostgreSQLMetadataRepository."""

import pytest

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import MetadataNotFoundError
from src.metadata.metadata_repository import MetadataRepositoryPort
from src.metadata.postgresql_adapter import PostgreSQLMetadataRepository


class TestPostgreSQLMetadataRepository:
    """Tests for PostgreSQLMetadataRepository."""

    def test_implements_metadata_repository_port(self):
        """PostgreSQLMetadataRepository implements MetadataRepositoryPort."""
        assert issubclass(PostgreSQLMetadataRepository, MetadataRepositoryPort)

    def test_store_and_get_roundtrip(
        self, metadata_repo: PostgreSQLMetadataRepository
    ):
        """store persists metadata and get retrieves the latest."""
        metadata_repo.clear_db()

        metadata = CredentialIssuerMetadata(
            credential_issuer="https://issuer.example.com",
            credential_endpoint="https://issuer.example.com/credential",
            credential_configurations_supported={},
        )

        metadata_repo.store(metadata)
        result = metadata_repo.get()

        assert result.credential_issuer == metadata.credential_issuer
        assert result.credential_endpoint == metadata.credential_endpoint

    def test_get_returns_most_recent(
        self, metadata_repo: PostgreSQLMetadataRepository
    ):
        """get returns the most recently stored metadata."""
        metadata_repo.clear_db()

        metadata1 = CredentialIssuerMetadata(
            credential_issuer="https://example1.com",
            credential_endpoint="https://example1.com/credential",
            credential_configurations_supported={},
        )
        metadata2 = CredentialIssuerMetadata(
            credential_issuer="https://example2.com",
            credential_endpoint="https://example2.com/credential",
            credential_configurations_supported={},
        )

        metadata_repo.store(metadata1)
        metadata_repo.store(metadata2)

        result = metadata_repo.get()
        assert result.credential_issuer == metadata2.credential_issuer

    def test_get_raises_metadata_not_found_error_when_empty(
        self, metadata_repo: PostgreSQLMetadataRepository
    ):
        """get raises MetadataNotFoundError when no metadata has been stored."""
        metadata_repo.clear_db()

        with pytest.raises(MetadataNotFoundError):
            _ = metadata_repo.get()

    def test_store_does_not_overwrite_existing(
        self, metadata_repo: PostgreSQLMetadataRepository
    ):
        """store adds new entries without overwriting existing ones."""
        metadata_repo.clear_db()

        metadata1 = CredentialIssuerMetadata(
            credential_issuer="https://example1.com",
            credential_endpoint="https://example1.com/credential",
            credential_configurations_supported={},
        )
        metadata2 = CredentialIssuerMetadata(
            credential_issuer="https://example2.com",
            credential_endpoint="https://example2.com/credential",
            credential_configurations_supported={},
        )

        metadata_repo.store(metadata1)
        first_result = metadata_repo.get()

        metadata_repo.store(metadata2)
        second_result = metadata_repo.get()

        # Both entries should exist, with different values
        assert first_result.credential_issuer == metadata1.credential_issuer
        assert second_result.credential_issuer == metadata2.credential_issuer

    def test_store_credentials_issuer_metadata_serialization(
        self, metadata_repo: PostgreSQLMetadataRepository
    ):
        """store and get work with full CredentialIssuerMetadata."""
        metadata_repo.clear_db()

        metadata = CredentialIssuerMetadata(
            credential_issuer="https://issuer.example.com",
            credential_endpoint="https://issuer.example.com/credential",
            credential_configurations_supported={},
        )

        metadata_repo.store(metadata)
        result = metadata_repo.get()

        # Verify we get back the same data
        assert result.credential_issuer == metadata.credential_issuer
        assert result.credential_endpoint == metadata.credential_endpoint
