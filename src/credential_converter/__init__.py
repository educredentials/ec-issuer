"""Credential converter domain package.

Provides the :class:`CredentialConverterPort` interface and an
:class:`HttpCredentialConverterAdapter` for converting OB3 credentials
to ELM/EDC format via an external converter service.
"""

from src.credential_converter.credential_converter_port import (
    CredentialConverterClientError,
    CredentialConverterPort,
)
from src.credential_converter.http_adapter import HttpCredentialConverterAdapter

__all__ = [
    "CredentialConverterClientError",
    "CredentialConverterPort",
    "HttpCredentialConverterAdapter",
]