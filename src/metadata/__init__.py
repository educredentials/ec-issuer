"""Metadata module.

Public exports:
- Domain models: CredentialIssuerMetadata and related types
- Port: MetadataRepositoryPort
- Service: MetadataService
- Errors: MetadataNotFoundError, MetadataSerializationError

Private (internal):
- Adapters: postgresql_adapter, ssi_agent_metadata_adapter
"""

from src.metadata.credential_issuer_metadata import CredentialIssuerMetadata
from src.metadata.metadata_repository import (
    MetadataNotFoundError,
    MetadataSerializationError,
)
from src.metadata.metadata_repository import MetadataRepositoryPort
from src.metadata.metadata_service import MetadataService

__all__ = [
    "CredentialIssuerMetadata",
    "MetadataNotFoundError",
    "MetadataSerializationError",
    "MetadataRepositoryPort",
    "MetadataService",
]
