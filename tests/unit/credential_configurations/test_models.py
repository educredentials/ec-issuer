"""Test models for credential configurations."""

import msgspec

from src.credential_configurations.models import (
    CredentialTemplate,
    Logo,
    Display,
)


class TestCredentialTemplate:
    def test_credential_template_from_obv3(self):
        """Test decoding a CredentialTemplate from OBv3 JSON."""
        config_json = msgspec.json.encode(
            {
                "credential_definition": {
                    "type": ["VerifiableCredential", "OpenBadgeCredential"]
                },
                "format": "vc+sd-jwt",
                "type": ["VerifiableCredential", "OpenBadgeCredential"],
            }
        )

        credential_template = msgspec.json.decode(config_json, type=CredentialTemplate)

        assert credential_template.id == ""
        assert credential_template.type == [
            "VerifiableCredential",
            "OpenBadgeCredential",
        ]

    def test_credential_template_with_obv3_metadata_fields(self):
        """Test decoding OBv3 fields like dataModel, tags, etc."""
        config_json = msgspec.json.encode(
            {
                "type": ["VerifiableCredential", "OpenBadgeCredential"],
                "format": "vc+sd-jwt",
                "dataModel": "open_badges_3-0",
                "creator": "eduCredentials",
                "holderType": "individual",
                "description": "eduCredentials OBv3 credentials",
                "tags": ["educredentials", "openbadge", "identity"],
                "status": "published",
                "visibility": "public",
            }
        )

        credential_template = msgspec.json.decode(config_json, type=CredentialTemplate)

        assert credential_template.type == [
            "VerifiableCredential",
            "OpenBadgeCredential",
        ]
        assert credential_template.dataModel == "open_badges_3-0"
        assert credential_template.creator == "eduCredentials"
        assert credential_template.holderType == "individual"
        assert credential_template.description == "eduCredentials OBv3 credentials"
        assert credential_template.tags == [
            "educredentials",
            "openbadge",
            "identity",
        ]
        assert credential_template.status == "published"
        assert credential_template.visibility == "public"

    def test_credential_template_display_info(self):
        """A credential template with a display section is decoded."""
        config_json = msgspec.json.encode(
            {
                "type": ["VerifiableCredential"],
                "format": "vc+sd-jwt",
                "display": {
                    "name": "eduCredential",
                    "logo": {
                        "uri": "https://example.com/logo.png",
                        "alt_text": "Logo",
                    },
                },
            }
        )

        credential_template = msgspec.json.decode(config_json, type=CredentialTemplate)

        assert credential_template.display is not None
        assert isinstance(credential_template.display, Display)
        assert credential_template.display.name == "eduCredential"
        assert credential_template.display.logo is not None
        assert isinstance(credential_template.display.logo, Logo)
        assert credential_template.display.logo.uri == "https://example.com/logo.png"
        assert credential_template.display.logo.alt_text == "Logo"

    def test_credential_template_minimal(self):
        """A credential template with only required fields is decoded."""
        config_json = msgspec.json.encode(
            {
                "type": ["VerifiableCredential"],
                "format": "jwt_vc_json",
            }
        )

        credential_template = msgspec.json.decode(config_json, type=CredentialTemplate)

        assert credential_template.type == ["VerifiableCredential"]
        assert credential_template.id == ""
        assert credential_template.dataModel is None
        assert credential_template.creator is None
        assert credential_template.holderType is None
        assert credential_template.description is None
        assert credential_template.tags is None
        assert credential_template.status is None
        assert credential_template.visibility is None

    def test_credential_template_display_is_none_when_absent(self):
        """Display is None when not present in JSON."""
        config_json = msgspec.json.encode(
            {
                "type": ["VerifiableCredential"],
                "format": "jwt_vc_json",
            }
        )

        credential_template = msgspec.json.decode(config_json, type=CredentialTemplate)

        assert credential_template.display is None
