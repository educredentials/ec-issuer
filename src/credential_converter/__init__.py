"""Credential converter domain package.

Provides the :class:`CredentialConverterPort` protocol, its
:class:`CredentialConverterClientError`, and an
:class:`HttpCredentialConverterAdapter` for converting OB3 credentials
to ELM/EDC format via an external converter service.
"""

from .credential_converter_port import (
    CredentialConverterClientError,
    CredentialConverterPort,
)
from .http_adapter import HttpCredentialConverterAdapter

__all__ = [
    "CredentialConverterClientError",
    "CredentialConverterPort",
    "HttpCredentialConverterAdapter",
]