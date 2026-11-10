"""Revocation module for managing credential revocation via SSI agent."""

from .revocation_client_port import CredentialRevocationError, RevocationClientPort
from .ssi_agent_revocation_client_adapter import SsiAgentRevocationClientAdapter

__all__ = [
    "CredentialRevocationError",
    "RevocationClientPort",
    "SsiAgentRevocationClientAdapter",
]
