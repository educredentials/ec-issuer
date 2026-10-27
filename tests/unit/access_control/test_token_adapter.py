"""Tests for the token-based access control adapter."""

import pytest

from src.access_control.token_adapter import TokenAccessControlAdapter


@pytest.fixture()
def adapter() -> TokenAccessControlAdapter:
    """Return a fresh TokenAccessControlAdapter."""
    return TokenAccessControlAdapter()


class TestTokenAccessControlAdapter:
    """Tests for TokenAccessControlAdapter."""

    def test_non_empty_token_grants_permission(
        self, adapter: TokenAccessControlAdapter
    ) -> None:
        """A non-empty bearer token grants permission."""
        assert adapter.may_import(
            bearer_token="some-token",
            resource_id="award-1",
            resource_type="Award",
            permission="import",
        ) is True

    def test_empty_token_denies_permission(
        self, adapter: TokenAccessControlAdapter
    ) -> None:
        """An empty bearer token denies permission."""
        assert adapter.may_import(
            bearer_token="",
            resource_id="award-1",
            resource_type="Award",
            permission="import",
        ) is False

    def test_whitespace_token_grants_permission(
        self, adapter: TokenAccessControlAdapter
    ) -> None:
        """A whitespace-only token is non-empty and grants permission.

        The actual empty/missing token guard happens at the HTTP adapter layer
        (_bearer_token raises MissingTokenError), so the access control adapter
        only sees non-empty strings.
        """
        assert adapter.may_import(
            bearer_token="   ",
            resource_id="award-1",
            resource_type="Award",
            permission="import",
        ) is True

    def test_args_ignored_for_logic(self, adapter: TokenAccessControlAdapter) -> None:
        """Resource type, permission, and resource_id do not affect the result."""
        assert adapter.may_import(
            bearer_token="token",
            resource_id="",
            resource_type="",
            permission="",
        ) is True