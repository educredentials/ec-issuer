"""Tests for CredentialTemplate bootstrap logic."""

from contextlib import AbstractContextManager
from pathlib import Path
from typing import override
from unittest.mock import patch

import pytest

from src.credential_configurations.bootstrap import resolve_credential_template_id
from src.credential_configurations.bootstrap import load_from_json
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
        mock_client = _MockClientPort(
            create_result=_make_template("", "json-id")
        )
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

        mock_client = _MockClientPort(
            create_result=_make_template("", "json-id")
        )
        with patch.dict(
            "os.environ",
            {
                "CREDENTIAL_TEMPLATE_JSON_FILE": str(json_file),
                "CREDENTIAL_TEMPLATE_ID": "env-fallback-id",
                "SSI_AGENT_URL": "http://agent.example.com",
            },
        ):
            with _patch_adapter(mock_client):
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

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with _patch_adapter(mock_client):
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

        with patch.dict("os.environ", {"SSI_AGENT_URL": "http://agent.example.com"}):
            with _patch_adapter(mock_client):
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

        with patch.dict(
            "os.environ",
            {"SSI_AGENT_URL": "http://broken.example.com"},
        ):
            with _patch_adapter(mock_client):
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
