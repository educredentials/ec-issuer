"""Token-based access control adapter.

Blocks anonymous (empty-token) requests. Real authorization is delegated to
the downstream awards service.
"""

from typing import override

from .access_control_port import AccessControlPort


class TokenAccessControlAdapter(AccessControlPort):
    """Adapter that grants permission only when a non-empty bearer token is present."""

    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        """Grant permission when bearer_token is non-empty.

        Args:
            bearer_token: The caller's bearer token.
            resource_id: The resource identifier (unused).
            resource_type: The resource type (unused).
            permission: The permission being checked (unused).

        Returns:
            True when bearer_token is non-empty, False otherwise.
        """
        return len(bearer_token) > 0