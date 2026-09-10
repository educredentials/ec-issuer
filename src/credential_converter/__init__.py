"""Credential converter domain package.

Provides :class:`HttpCredentialConverterAdapter` for converting OB3 credentials
to ELM/EDC format via an external converter service.
"""

from src.credential_converter.http_adapter import (
    CredentialConverterClientError,
    HttpCredentialConverterAdapter,
)

__all__ = [
    "CredentialConverterClientError",
    "HttpCredentialConverterAdapter",
]