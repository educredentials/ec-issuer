"""Sysadmin service implementing administrative operations."""

from .sysadmin_port import SysadminPort


class SysadminService(SysadminPort):
    """Service that executes sysadmin operations against the metadata repository."""

    def __init__(self) -> None:
        """ """
