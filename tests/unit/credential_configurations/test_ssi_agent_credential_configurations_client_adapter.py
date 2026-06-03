"""Unit tests for CredentialConfigurationsClient Stub and Spy."""

import pytest

from src.credential_configurations.credential_configurations_client_port import (
    CredentialConfigurationNotFound,
)
from src.credential_configurations.models import (
    CredentialConfiguration,
    Display,
)
from ..test_doubles import (
    CredentialConfigurationsClientStub,
    CredentialConfigurationsClientSpy,
)


class TestCredentialConfigurationsClientStub:
    """Tests for CredentialConfigurationsClientStub."""

    def test_create_stores_and_returns_configuration(self):
        """create stores the configuration and returns it."""
        client = CredentialConfigurationsClientStub()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )

        _ = client.create(configuration)

        result = client.get("test-id")
        assert result.credential_configuration_id == "test-id"
        assert result.format == "jwt_vc_json"

    def test_get_returns_stored_configuration(self):
        """get returns a stored configuration."""
        client = CredentialConfigurationsClientStub()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )
        _ = client.create(configuration)

        result = client.get("test-id")

        assert result.credential_configuration_id == "test-id"

    def test_get_not_found(self):
        """get raises CredentialConfigurationNotFound when not found."""
        client = CredentialConfigurationsClientStub()

        with pytest.raises(CredentialConfigurationNotFound):
            _ = client.get("nonexistent")

    def test_list_returns_all_configurations(self):
        """list returns all stored configurations."""
        client = CredentialConfigurationsClientStub()
        config1 = CredentialConfiguration(
            credential_configuration_id="test-id-1",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test 1")],
        )
        config2 = CredentialConfiguration(
            credential_configuration_id="test-id-2",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test 2")],
        )
        _ = client.create(config1)
        _ = client.create(config2)

        results = client.list()

        assert len(results) == 2
        ids = [r.credential_configuration_id for r in results]
        assert "test-id-1" in ids
        assert "test-id-2" in ids

    def test_update_existing_configuration(self):
        """update updates an existing configuration."""
        client = CredentialConfigurationsClientStub()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Original")],
        )
        _ = client.create(configuration)

        updated_config = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Updated")],
        )
        result = client.update(updated_config)

        assert result.display is not None
        assert result.display[0].name == "Updated"

    def test_update_not_found(self):
        """update raises CredentialConfigurationNotFound when not found."""
        client = CredentialConfigurationsClientStub()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )

        with pytest.raises(CredentialConfigurationNotFound):
            _ = client.update(configuration)

    def test_delete_existing_configuration(self):
        """delete removes an existing configuration."""
        client = CredentialConfigurationsClientStub()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )
        _ = client.create(configuration)

        client.delete("test-id")

        with pytest.raises(CredentialConfigurationNotFound):
            _ = client.get("test-id")

    def test_delete_not_found(self):
        """delete raises CredentialConfigurationNotFound when not found."""
        client = CredentialConfigurationsClientStub()

        with pytest.raises(CredentialConfigurationNotFound):
            client.delete("nonexistent")


class TestCredentialConfigurationsClientSpy:
    """Tests for CredentialConfigurationsClientSpy."""

    def test_create_records_call(self):
        """create records the call."""
        client = CredentialConfigurationsClientSpy()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )

        _ = client.create(configuration)

        assert len(client.calls) == 1
        assert client.calls[0][0] == "create"
        # The second element is the configuration
        call_arg = client.calls[0][1]
        assert isinstance(call_arg, CredentialConfiguration)
        assert call_arg.credential_configuration_id == "test-id"

    def test_get_records_call(self):
        """get records the call."""
        client = CredentialConfigurationsClientSpy()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )
        _ = client.create(configuration)

        _ = client.get("test-id")

        assert len(client.calls) == 2
        assert client.calls[1][0] == "get"
        call_arg = client.calls[1][1]
        assert isinstance(call_arg, str)
        assert call_arg == "test-id"

    def test_list_records_call(self):
        """list records the call."""
        client = CredentialConfigurationsClientSpy()

        _ = client.list()

        assert len(client.calls) == 1
        assert client.calls[0][0] == "list"

    def test_update_records_call(self):
        """update records the call."""
        client = CredentialConfigurationsClientSpy()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )
        _ = client.create(configuration)

        updated_config = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Updated")],
        )
        _ = client.update(updated_config)

        assert len(client.calls) == 2
        assert client.calls[1][0] == "update"

    def test_delete_records_call(self):
        """delete records the call."""
        client = CredentialConfigurationsClientSpy()
        configuration = CredentialConfiguration(
            credential_configuration_id="test-id",
            format="jwt_vc_json",
            display=[Display(locale="en", name="Test")],
        )
        _ = client.create(configuration)

        client.delete("test-id")

        assert len(client.calls) == 2
        assert client.calls[1][0] == "delete"
        call_arg = client.calls[1][1]
        assert isinstance(call_arg, str)
        assert call_arg == "test-id"
