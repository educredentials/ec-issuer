"""Sysadmin port defining the administrative operations interface."""

from abc import ABC, abstractmethod


class SysadminPort(ABC):
    """Port for administrative operations on the EC Issuer."""

    @abstractmethod
    def run(self, command: list[str]) -> None:
        """Run a sysadmin command.

        Args:
            command: The command and its arguments.
        """
        ...
