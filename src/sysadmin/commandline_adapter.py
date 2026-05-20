"""Command-line adapter for sysadmin operations."""

import sys

from .sysadmin_service import SysadminService

_USAGE = """\
Usage: ec-issuer-cli <command> [args]

Commands:
    - None yet
"""


def main() -> None:
    """Entry point for the ec-issuer-cli command."""
    _service = SysadminService()
    match sys.argv[1:]:
        case ["todo"]:
            pass
        case _:
            print(_USAGE, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
