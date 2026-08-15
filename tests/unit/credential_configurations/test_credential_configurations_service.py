"""Tests for CredentialTemplateService."""

from typing import override

import requests
import pytest

from src.credential_configurations.credential_configurations_client_port import (
    CredentialTemplateClientError,
    CredentialTemplateClientPort,
)
from src.credential_configurations.credential_configurations_service import (
    CredentialTemplateService,
)
from src.credential_configurations.models import CredentialTemplate


def _make_template(title: str = "My Template") -> CredentialTemplate:
    return CredentialTemplate(
        id="",
        title=title,
        type=["VerifiableCredential"],
    )


def _empty_template() -> CredentialTemplate:
    return CredentialTemplate(id="", title="", type=[])


class _CredentialTemplateClientStub(CredentialTemplateClientPort):
    """Typed stub for CredentialTemplateClientPort used in tests."""

    _list_result: list[CredentialTemplate]
    _create_result: CredentialTemplate
    _list_side_effect: Exception | None
    _create_side_effect: Exception | None
    list_called: bool
    create_called: bool

    def __init__(
        self,
        list_result: list[CredentialTemplate],
        create_result: CredentialTemplate,
        list_side_effect: Exception | None = None,
        create_side_effect: Exception | None = None,
    ) -> None:
        self._list_result = list_result
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
        return self._create_result

    @override
    def get(self, template_id: str) -> CredentialTemplate:
        raise NotImplementedError

    @override
    def update(self, configuration: CredentialTemplate) -> CredentialTemplate:
        raise NotImplementedError

    @override
    def delete(self, template_id: str) -> None:
        raise NotImplementedError


def _make_stub(
    list_result: list[CredentialTemplate],
    create_result: CredentialTemplate,
    list_side_effect: Exception | None = None,
    create_side_effect: Exception | None = None,
) -> _CredentialTemplateClientStub:
    return _CredentialTemplateClientStub(
        list_result=list_result,
        create_result=create_result,
        list_side_effect=list_side_effect,
        create_side_effect=create_side_effect,
    )


class TestCredentialTemplateServiceEnsureById:
    """Tests for credential template service ensure_by_title method."""

    def test_returns_existing_when_title_matches(self) -> None:
        """Returns existing template if title matches a listed one."""
        existing = _make_template(title="Existing")
        existing.id = "Existing"
        stub = _make_stub(
            list_result=[existing],
            create_result=_make_template(title="Should Not Be Called"),
        )
        service = CredentialTemplateService(client=stub)
        result = service.ensure_by_title(_make_template(title="Existing"))

        assert result.id == "Existing"
        assert result.title == "Existing"
        assert stub.list_called
        assert not stub.create_called

    def test_creates_when_no_title_match(self) -> None:
        """Creates a new template when no title matches a listed one."""
        existing = _make_template(title="Other")
        created = _make_template(title="New")
        created.id = "created-id"
        stub = _make_stub(
            list_result=[existing],
            create_result=created,
        )
        service = CredentialTemplateService(client=stub)
        result = service.ensure_by_title(created, ssi_agent_url="http://agent.example.com")

        assert result.id == "created-id"
        assert stub.list_called
        assert stub.create_called

    def test_creates_when_list_is_empty(self) -> None:
        """Creates a new template when no templates exist."""
        created = _make_template(title="New")
        created.id = "created-id"
        stub = _make_stub(list_result=[], create_result=created)
        service = CredentialTemplateService(client=stub)
        result = service.ensure_by_title(created)

        assert result.id == "created-id"

    def test_raises_runtime_error_on_list_transport_error(self) -> None:
        """List raises RuntimeError when SSI Agent is unreachable."""
        stub = _make_stub(
            list_result=[],
            create_result=_empty_template(),
            list_side_effect=requests.RequestException("connection refused"),
        )
        service = CredentialTemplateService(client=stub)

        url = "http://broken.example.com"
        with pytest.raises(RuntimeError) as exc_info:
            _ = service.ensure_by_title(_make_template("New"), ssi_agent_url=url)

        msg = f"Failed to reach SSI Agent {url}"
        assert msg in str(exc_info.value)

    def test_raises_runtime_error_on_list_client_error(self) -> None:
        """List raises RuntimeError when client raises CredentialTemplateClientError."""
        stub = _make_stub(
            list_result=[],
            create_result=_empty_template(),
            list_side_effect=CredentialTemplateClientError("API error"),
        )
        service = CredentialTemplateService(client=stub)

        with pytest.raises(RuntimeError) as exc_info:
            _ = service.ensure_by_title(_make_template("New"))

        assert "Failed to reach SSI Agent" in str(exc_info.value)
        assert "API error" in str(exc_info.value)

    def test_raises_runtime_error_on_create_transport_error(self) -> None:
        """Create raises RuntimeError when SSI Agent is unreachable."""
        stub = _make_stub(
            list_result=[],
            create_result=_empty_template(),
            create_side_effect=requests.Timeout("Timed out"),
        )
        service = CredentialTemplateService(client=stub)

        url = "http://agent.example.com"
        with pytest.raises(RuntimeError) as exc_info:
            _ = service.ensure_by_title(_make_template("New"), ssi_agent_url=url)

        msg = f"Failed to create credential template on {url}"
        assert msg in str(exc_info.value)

    def test_raises_runtime_error_on_create_client_error(self) -> None:
        """Create raises RuntimeError on CredentialTemplateClientError."""
        stub = _make_stub(
            list_result=[],
            create_result=_empty_template(),
            create_side_effect=CredentialTemplateClientError(
                "Upstream error: 400 Bad Request",
            ),
        )
        service = CredentialTemplateService(client=stub)

        with pytest.raises(RuntimeError) as exc_info:
            _ = service.ensure_by_title(_make_template("New"))

        assert "Failed to create credential template" in str(exc_info.value)
        assert "Upstream error: 400 Bad Request" in str(exc_info.value)

    def test_returns_existing_even_if_create_fails(self) -> None:
        """Skips creation when a matching template already exists."""
        existing = _make_template(title="Found")
        existing.id = "Found"
        stub = _make_stub(
            list_result=[existing],
            create_result=_empty_template(),
            create_side_effect=CredentialTemplateClientError("Should not be called"),
        )
        service = CredentialTemplateService(client=stub)
        result = service.ensure_by_title(_make_template(title="Found"))

        assert result.id == "Found"
        assert stub.list_called
        assert not stub.create_called
