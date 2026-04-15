"""Hardcoded adapter for access control that always grants permission."""

from typing import override

from src.access_control.access_control_port import AccessControlPort


class HardcodedAccessControlAdapter(AccessControlPort):
    """Adapter that always grants any permission request."""

    @override
    def may_import(
        self, bearer_token: str, resource_id: str, resource_type: str, permission: str
    ) -> bool:
        """Always return True regardless of the arguments.

        Args:
            bearer_token: The caller's bearer token (unused).
            resource_id: The resource identifier (unused).
            resource_type: The resource type (unused).
            permission: The permission being checked (unused).

        Returns:
            Always True.
        """
        return True
