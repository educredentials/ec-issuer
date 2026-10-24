"""Tests for the ExtensionContextServer trust-boundary module."""

from pathlib import Path

from src.api.extension_context_server import ExtensionContextServer


class TestExtensionContextServer:
    """Tests for ExtensionContextServer.serve()."""

    @staticmethod
    def _create_tmp_dir(tmp_path: Path) -> Path:
        """Create a temp extensions dir with a minimal context file."""
        ext_dir = tmp_path / "extensions"
        ext_dir.mkdir()
        lang_dir = ext_dir / "LanguageExtension"
        lang_dir.mkdir()
        _ = (lang_dir / "context.json").write_text(
            '{"@context": "${BASE_URL}/static/extensions/test"}',
            encoding="utf-8",
        )
        return ext_dir

    def test_serves_valid_context_file(self, tmp_path: Path) -> None:
        """Serve a valid context.json file returns 200 with correct headers."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        content, status_code, headers = server.serve(
            "LanguageExtension/context.json"
        )
        assert status_code == 200
        assert headers["Content-Type"] == "application/ld+json"
        assert "${BASE_URL}" not in content

    def test_replaces_base_url_placeholder(self, tmp_path: Path) -> None:
        """The ${BASE_URL} placeholder is replaced with the configured URL."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="https://edu.example.com",
            extensions_dir=str(ext_dir),
        )
        content, status_code, _ = server.serve(
            "LanguageExtension/context.json"
        )
        assert status_code == 200
        assert "https://edu.example.com/static/extensions/test" in content

    def test_returns_404_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Non-existent extension file returns 404."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        _, status_code, _ = server.serve("MissingExtension/context.json")
        assert status_code == 404

    def test_returns_404_for_non_matching_filename(self, tmp_path: Path) -> None:
        """Files not matching pattern return 404."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        _, status_code, _ = server.serve("some/random/file.txt")
        assert status_code == 404

    def test_returns_404_for_path_traversal(self, tmp_path: Path) -> None:
        """Path traversal attempts return 404."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        _, status_code, _ = server.serve("../etc/passwd/context.json")
        assert status_code == 404

    def test_returns_404_for_upward_traversal_inside_dir(self, tmp_path: Path) -> None:
        """Traversal that escapes extensions_dir returns 404."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        _, status_code, _ = server.serve("LanguageExtension/../../../etc/hostname")
        assert status_code == 404

    def test_rejects_unsupported_extension(self, tmp_path: Path) -> None:
        """Files with unsupported extensions return 404."""
        ext_dir = self._create_tmp_dir(tmp_path)
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        _, status_code, _ = server.serve("LanguageExtension/notes.txt")
        assert status_code == 404

    def test_serves_schema_file(self, tmp_path: Path) -> None:
        """A schema.json file can be served."""
        ext_dir = self._create_tmp_dir(tmp_path)
        schema_dir = ext_dir / "TestExtension"
        schema_dir.mkdir()
        _ = (schema_dir / "schema.json").write_text(
            '{"$schema": "test"}', encoding="utf-8"
        )
        server = ExtensionContextServer(
            base_url="http://localhost:8000",
            extensions_dir=str(ext_dir),
        )
        _, status_code, headers = server.serve("TestExtension/schema.json")
        assert status_code == 200
        assert headers["Content-Type"] == "application/ld+json"