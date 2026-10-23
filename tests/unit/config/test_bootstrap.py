"""Tests for CredentialTemplate bootstrap logic."""

from contextlib import AbstractContextManager
from pathlib import Path
from typing import override
from unittest.mock import patch

import pytest

from src.credential_configurations.bootstrap import (
    load_from_directory,
    load_from_json,
    resolve_credential_template_id,
    resolve_credential_template_ids,
)
from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateClientError,
    CredentialTemplateClientPort,
)
from src.credential_configurations.models import CredentialTemplate


class _MockClientPort(CredentialTemplateClientPort):
    """Typed stub implementing CredentialTemplateClientPort."""

    _list_result: list[CredentialTemplate]
    _create_result: CredentialTemplate | None
    _list_side_effect: Exception | None
    _create_side_effect: Exception | None
    list_called: bool
    create_called: bool

    def __init__(
        self,
        list_result: list[CredentialTemplate] | None = None,
        create_result: CredentialTemplate | None = None,
        list_side_effect: Exception | None = None,
        create_side_effect: Exception | None = None,
    ) -> None:
        self._list_result = list_result or []
        self._create_result = create_result
        self._list_side_effect = list_side_effect
        self._create_side_effect = create_side_effect
        self.list_called = False
        self.create_called = False

    @override
    def list(self) -> list[CredentialTemplate]:
        self.list_called = True
        if self._list_side_effect:
            raise self._list_side_effect
        return self._list_result

    @override
    def create(self, template: CredentialTemplate) -> CredentialTemplate:
        self.create_called = True
        if self._create_side_effect:
            raise self._create_side_effect
        if self._create_result is not None:
            return self._create_result
        return template

    @override
    def get(self, template_id: str) -> CredentialTemplate:
        raise NotImplementedError

    @override
    def update(self, configuration: CredentialTemplate) -> CredentialTemplate:
        raise NotImplementedError

    @override
    def delete(self, template_id: str) -> None:
        raise NotImplementedError

    def ensure_by_title(
        self, _template: CredentialTemplate, _ssi_agent_url: str = ""
    ) -> CredentialTemplate:
        raise NotImplementedError


def _make_template(title: str, template_id: str) -> CredentialTemplate:
    return CredentialTemplate(id=template_id, title=title, type=[])


def _patch_adapter(
    mock_client: _MockClientPort,
) -> AbstractContextManager[None]:
    return patch(
        "src.credential_configurations.bootstrap."
        + "ssi_cred_client.SsiAgentCredentialTemplateClientAdapter",
        return_value=mock_client,
    )


class TestResolveCredentialTemplateId:
    """Tests for resolve_credential_template_id function."""

    def test_uses_json_file_when_set(self, tmp_path: Path) -> None:
        """CREDENTIAL_TEMPLATE_JSON_FILE is preferred over env var."""
        json_file = tmp_path / "template.json"
        _ = json_file.write_text('{"title": "Test", "type": []}')

        env_with_json = {
            "CREDENTIAL_TEMPLATE_JSON_FILE": str(json_file),
            "CREDENTIAL_TEMPLATE_ID": "env-fallback-id",
            "SSI_AGENT_URL": "http://agent.example.com",
        }
        mock_client = _MockClientPort(create_result=_make_template("", "json-id"))
        with patch.dict("os.environ", env_with_json):
            with _patch_adapter(mock_client):
                resolved_id = resolve_credential_template_id()

        assert resolved_id == "json-id"

    def test_uses_env_var_when_no_json_file(self) -> None:
        """Falls back to CREDENTIAL_TEMPLATE_ID when JSON file not set."""
        with patch.dict(
            "os.environ",
            {
                "CREDENTIAL_TEMPLATE_ID": "env-resolved-id",
                "CREDENTIAL_TEMPLATE_JSON_FILE": "",
            },
        ):
            resolved_id = resolve_credential_template_id()
            assert resolved_id == "env-resolved-id"

    def test_raises_runtime_error_when_no_config(self) -> None:
        """Raises RuntimeError when neither JSON file nor env var is set."""
        with patch.dict(
            "os.environ",
            {
                "CREDENTIAL_TEMPLATE_JSON_FILE": "",
                "CREDENTIAL_TEMPLATE_ID": "",
            },
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _ = resolve_credential_template_id()

            assert "No credential configuration ID configured" in str(exc_info.value)

    def test_ignores_empty_env_values(self) -> None:
        """Empty string env values are treated as not set."""
        with patch.dict(
            "os.environ",
            {
                "CREDENTIAL_TEMPLATE_JSON_FILE": "",
                "CREDENTIAL_TEMPLATE_ID": "   ",
            },
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _ = resolve_credential_template_id()

            assert "No credential configuration ID configured" in str(exc_info.value)

    def test_json_file_takes_precedence(self, tmp_path: Path) -> None:
        """JSON file env var takes precedence even when template ID is also set."""
        json_file = tmp_path / "template.json"
        _ = json_file.write_text('{"title": "Test", "type": []}')

        mock_client = _MockClientPort(create_result=_make_template("", "json-id"))
        with (
            patch.dict(
                "os.environ",
                {
                    "CREDENTIAL_TEMPLATE_JSON_FILE": str(json_file),
                    "CREDENTIAL_TEMPLATE_ID": "env-fallback-id",
                    "SSI_AGENT_URL": "http://agent.example.com",
                },
            ),
            _patch_adapter(mock_client),
        ):
            resolved_id = resolve_credential_template_id()

        assert resolved_id == "json-id"


class TestLoadFromJson:
    """Tests for load_from_json function."""

    def test_missing_file_raises_runtime_error(self) -> None:
        """FileNotFoundError is wrapped in RuntimeError with file path."""
        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with pytest.raises(RuntimeError) as exc_info:
                _ = load_from_json("/nonexistent/path.json")

            assert "/nonexistent/path.json" in str(exc_info.value)

    def test_invalid_json_raises_runtime_error(self, tmp_path: Path) -> None:
        """Invalid JSON is wrapped in RuntimeError with file path."""
        json_file = tmp_path / "invalid.json"
        _ = json_file.write_text("{ this is not valid json }")

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with pytest.raises(RuntimeError) as exc_info:
                _ = load_from_json(str(json_file))

            assert str(json_file) in str(exc_info.value)

    def test_missing_title_raises_runtime_error(self, tmp_path: Path) -> None:
        """Empty title field raises RuntimeError."""
        json_file = tmp_path / "no_title.json"
        _ = json_file.write_text('{"type": []}')

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with pytest.raises(RuntimeError) as exc_info:
                _ = load_from_json(str(json_file))

            assert "missing a non-empty 'title'" in str(exc_info.value)

    def test_whitespace_title_raises_runtime_error(self, tmp_path: Path) -> None:
        """Whitespace-only title is treated as missing."""
        json_file = tmp_path / "whitespace.json"
        _ = json_file.write_text('{"title": "   ", "type": []}')

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with pytest.raises(RuntimeError) as exc_info:
                _ = load_from_json(str(json_file))

            assert "missing a non-empty 'title'" in str(exc_info.value)

    def test_finds_existing_template_by_title(self, tmp_path: Path) -> None:
        """Existing template with matching title is returned."""
        json_file = tmp_path / "existing.json"
        _ = json_file.write_text('{"title": "Existing", "type": []}')

        return_template = _make_template("Existing", "found-id")
        mock_client = _MockClientPort(
            list_result=[return_template],
        )

        with (
            patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}),
            _patch_adapter(mock_client),
        ):
            result = load_from_json(str(json_file))

        assert mock_client.list_called
        assert not mock_client.create_called
        assert result == "found-id"

    def test_creates_new_template_when_not_found(self, tmp_path: Path) -> None:
        """Creates new template when no title match is found."""
        json_file = tmp_path / "new_template.json"
        _ = json_file.write_text('{"title": "New", "type": []}')

        return_template = _make_template("New", "new-id")
        mock_client = _MockClientPort(
            list_result=[],
            create_result=return_template,
        )

        with (
            patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}),
            _patch_adapter(mock_client),
        ):
            result = load_from_json(str(json_file))

        assert mock_client.list_called
        assert mock_client.create_called
        assert result == "new-id"

    def test_fails_on_ssi_agent_connect_error(self, tmp_path: Path) -> None:
        """SSI Agent connection error is wrapped in RuntimeError."""
        json_file = tmp_path / "agent_err.json"
        _ = json_file.write_text('{"title": "Cred", "type": []}')

        mock_client = _MockClientPort(
            list_result=[],
            create_result=_make_template("", ""),
            list_side_effect=RuntimeError(
                "Failed to reach SSI Agent "
                + "http://broken.example.com: Connection refused"
            ),
        )

        with (
            patch.dict(
                "os.environ",
                {"SSI_AGENT_URL": "http://broken.example.com"},
            ),
            _patch_adapter(mock_client),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _ = load_from_json(str(json_file))

            assert "Failed to reach SSI Agent" in str(exc_info.value)
            assert "broken.example.com" in str(exc_info.value)

    def test_fails_on_ssi_agent_create_error(self, tmp_path: Path) -> None:
        """Create failure is wrapped in RuntimeError."""
        json_file = tmp_path / "create_fail.json"
        _ = json_file.write_text('{"title": "Cred", "type": []}')

        mock_client = _MockClientPort(
            list_result=[],
            create_result=_make_template("", ""),
            create_side_effect=CredentialTemplateClientError(
                "Upstream error: 400 Bad Request"
            ),
        )

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with _patch_adapter(mock_client):
                with pytest.raises(RuntimeError) as exc_info:
                    _ = load_from_json(str(json_file))

                assert "Failed to create credential template" in str(exc_info.value)
                assert "Bad Request" in str(exc_info.value)

    def test_fails_when_create_returns_no_id(self, tmp_path: Path) -> None:
        """Create returning empty ID raises RuntimeError."""
        json_file = tmp_path / "no_id.json"
        _ = json_file.write_text('{"title": "No ID", "type": []}')

        return_template = _make_template("No ID", "")
        mock_client = _MockClientPort(
            list_result=[],
            create_result=return_template,
        )

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with _patch_adapter(mock_client):
                with pytest.raises(RuntimeError) as exc_info:
                    _ = load_from_json(str(json_file))

                assert "with no ID" in str(exc_info.value)


class TestResolveCredentialTemplateIds:
    """Tests for resolve_credential_template_ids function."""

    def test_uses_json_dir_when_set(self, tmp_path: Path) -> None:
        """CREDENTIAL_TEMPLATE_JSON_DIR is preferred over single-file mode."""
        json_dir = tmp_path / "templates"
        json_dir.mkdir()
        json_files = [
            json_dir / "template1.json",
            json_dir / "template2.json",
        ]
        _ = json_files[0].write_text('{"title": "Template One", "type": []}')
        _ = json_files[1].write_text('{"title": "Template Two", "type": []}')

        mock_client = _MockClientPort(
            list_result=[
                _make_template("Template One", "id-one"),
                _make_template("Template Two", "id-two"),
            ],
        )

        with (
            patch.dict(
                "os.environ",
                {
                    "CREDENTIAL_TEMPLATE_JSON_DIR": str(json_dir),
                    "CREDENTIAL_TEMPLATE_JSON_FILE": "",
                    "CREDENTIAL_TEMPLATE_ID": "",
                    "SSI_AGENT_URL": "http://agent.example.com",
                },
            ),
            _patch_adapter(mock_client),
        ):
            resolved_ids = resolve_credential_template_ids()

        assert resolved_ids == ["id-one", "id-two"]

    def test_falls_back_to_single_file_mode(self, tmp_path: Path) -> None:
        """Without JSON_DIR, falls back to single-file resolve."""
        json_file = tmp_path / "template.json"
        _ = json_file.write_text('{"title": "Single", "type": []}')

        mock_client = _MockClientPort(
            create_result=_make_template("Single", "single-id"),
        )

        with (
            patch.dict(
                "os.environ",
                {
                    "CREDENTIAL_TEMPLATE_JSON_DIR": "",
                    "CREDENTIAL_TEMPLATE_JSON_FILE": str(json_file),
                    "CREDENTIAL_TEMPLATE_ID": "",
                    "SSI_AGENT_URL": "http://agent.example.com",
                },
            ),
            _patch_adapter(mock_client),
        ):
            resolved_ids = resolve_credential_template_ids()

        assert resolved_ids == ["single-id"]

    def test_falls_back_to_env_var_when_no_json(self) -> None:
        """Without any JSON config, falls back to CREDENTIAL_TEMPLATE_ID."""
        with patch.dict(
            "os.environ",
            {
                "CREDENTIAL_TEMPLATE_JSON_DIR": "",
                "CREDENTIAL_TEMPLATE_JSON_FILE": "",
                "CREDENTIAL_TEMPLATE_ID": "env-fallback-id",
            },
        ):
            resolved_ids = resolve_credential_template_ids()
            assert resolved_ids == ["env-fallback-id"]


class TestLoadFromDirectory:
    """Tests for load_from_directory function."""

    def test_missing_directory_raises_runtime_error(self) -> None:
        """Non-existent directory raises RuntimeError with directory path."""
        with pytest.raises(RuntimeError) as exc_info:
            _ = load_from_directory("/nonexistent/path")

        assert "/nonexistent/path" in str(exc_info.value)

    def test_empty_directory_raises_runtime_error(self, tmp_path: Path) -> None:
        """Directory with no .json files raises RuntimeError."""
        json_dir = tmp_path / "empty_templates"
        json_dir.mkdir()

        with pytest.raises(RuntimeError) as exc_info:
            _ = load_from_directory(str(json_dir))

        assert str(json_dir) in str(exc_info.value)

    def test_loads_all_json_files(self, tmp_path: Path) -> None:
        """All .json files in directory are loaded."""
        json_dir = tmp_path / "templates"
        json_dir.mkdir()

        template1 = json_dir.joinpath("template1.json")
        template2 = json_dir.joinpath("template2.json")
        template3 = json_dir.joinpath("template3.json")
        # Non-JSON file should be ignored
        _ = json_dir.joinpath("readme.txt").write_text("not a template")

        _ = template1.write_text('{"title": "One", "type": []}')
        _ = template2.write_text('{"title": "Two", "type": []}')
        _ = template3.write_text('{"title": "Three", "type": []}')

        mock_client = _MockClientPort(
            list_result=[
                _make_template("One", "id-one"),
                _make_template("Two", "id-two"),
                _make_template("Three", "id-three"),
            ],
        )

        with (
            patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}),
            _patch_adapter(mock_client),
        ):
            result = load_from_directory(str(json_dir))

        assert len(result) == 3
        assert result == ["id-one", "id-two", "id-three"]

    def test_json_files_loaded_in_sorted_order(self, tmp_path: Path) -> None:
        """Files are loaded in sorted filename order."""
        json_dir = tmp_path / "templates"
        json_dir.mkdir()

        # Create files that won't sort alphabetically
        _ = json_dir.joinpath("z_template.json").write_text(
            '{"title": "Z", "type": []}'
        )
        _ = json_dir.joinpath("a_template.json").write_text(
            '{"title": "A", "type": []}'
        )

        mock_client = _MockClientPort(
            list_result=[
                _make_template("A", "a-id"),
                _make_template("Z", "z-id"),
            ],
        )

        with (
            patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}),
            _patch_adapter(mock_client),
        ):
            result = load_from_directory(str(json_dir))

        # Sorted alphabetically: a_template.json before z_template.json
        assert result == ["a-id", "z-id"]

    def test_missing_title_in_any_file_raises(self, tmp_path: Path) -> None:
        """Missing title in any file raises RuntimeError."""
        json_dir = tmp_path / "templates"
        json_dir.mkdir()

        _ = json_dir.joinpath("good.json").write_text('{"title": "Good", "type": []}')
        _ = json_dir.joinpath("no_title.json").write_text('{"type": []}')

        # Mock create with a valid ID so "no ID" error doesn't mask the
        # "missing title" error we're testing for (second file)
        mock_client = _MockClientPort(
            list_result=[],
            create_result=_make_template("Good", "good-id"),
        )

        with (
            patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}),
            _patch_adapter(mock_client),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _ = load_from_directory(str(json_dir))

            assert "missing a non-empty 'title'" in str(exc_info.value)
            assert "no_title.json" in str(exc_info.value)

    def test_creates_templates_when_not_found(self, tmp_path: Path) -> None:
        """Templates are created when they don't exist on SSI Agent."""
        json_dir = tmp_path / "templates"
        json_dir.mkdir()
        _ = json_dir.joinpath("new.json").write_text('{"title": "New", "type": []}')

        mock_client = _MockClientPort(
            list_result=[],
            create_result=_make_template("New", "new-id"),
        )

        with (
            patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}),
            _patch_adapter(mock_client),
        ):
            result = load_from_directory(str(json_dir))

        assert mock_client.list_called
        assert mock_client.create_called
        assert result == ["new-id"]
