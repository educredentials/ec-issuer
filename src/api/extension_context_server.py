"""Serve JSON-LD extension contexts for credential validation.

This module owns all trust-boundary logic for serving extension files:
name-pattern checking, ``realpath`` containment checks, ``${BASE_URL}``
substitution, and disk reads.  No environment variable reads — all
configuration is injected from ``EnvConfigRepo`` at application bootstrap.
"""

import re
from pathlib import Path


class ExtensionContextServer:
    """Serve JSON-LD extension contexts from a filesystem directory.

    Only files under ``extensions_dir`` are served.  The ``${BASE_URL}``
    placeholder in context files is replaced with ``base_url`` so that
    generated credentials carry the correct absolute URLs for their
    validation schemas.
    """

    _base_url: str
    _extensions_dir: str
    _filename_pattern: re.Pattern[str]

    def __init__(
        self,
        base_url: str,
        extensions_dir: str,
    ) -> None:
        """Initialise the extension context server.

        Args:
            base_url: The public base URL of this issuer (for ``${BASE_URL}``
                substitution).
            extensions_dir: Absolute path to the directory containing
                extension context and schema files.
        """
        self._base_url = base_url.rstrip("/")
        self._extensions_dir = extensions_dir
        self._filename_pattern = re.compile(
            r"^[A-Za-z0-9_-]+/(context|schema)\.json$"
        )

    def serve(self, filename: str) -> tuple[str, int, dict[str, str]]:
        """Serve an extension context or schema file.

        Args:
            filename: The path component after ``/static/extensions/``.

        Returns:
            A tuple of (content, status_code, headers).
            On failure the status code is 404 and content is a short message.
        """
        if not self._filename_pattern.match(filename):
            return "not found", 404, {}

        path = Path(self._extensions_dir) / filename
        resolved = path.resolve()
        ext_dir_resolved = Path(self._extensions_dir).resolve()

        if not resolved.is_relative_to(ext_dir_resolved):
            return "not found", 404, {}

        if not resolved.is_file():
            return "not found", 404, {}

        try:
            content = resolved.read_text(encoding="utf-8")
        except OSError:
            return "not found", 404, {}

        content = content.replace("${BASE_URL}", self._base_url)

        return content, 200, {"Content-Type": "application/ld+json"}