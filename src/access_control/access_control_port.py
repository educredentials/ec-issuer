"""Port for access control adapters."""

from abc import ABC, abstractmethod


class AccessControlPort(ABC):
    """Port: access control interface for checking resource permissions."""

    @abstractmethod
    def may_import(
        self, bearer_token: str, resource_id: str, resource_type: str, permission: str
    ) -> bool:
        """Check whether the caller may perform an action on a resource.

        Args:
            bearer_token: The caller's bearer token.
            resource_id: The identifier of the resource being accessed.
            resource_type: The type of the resource (e.g. "Award").
            permission: The permission being checked (e.g. "import").

        Returns:
            True when the action is permitted, False otherwise.
        """
        ...
