"""Test models for credential configurations."""

import msgspec

from src.credential_configurations.models import (
    CredentialConfiguration,
)


class TestCredentialConfiguration:
    def test_credential_configuration_from_metadata(self):
        """
        Test that credential_configuration_from handles an openid credential
        configuration
        """
        supported_config_json = msgspec.json.encode(
            {
                "credential_definition": {
                    "type": ["VerifiableCredential", "OpenBadgeCredential"]
                },
                "credential_metadata": {
                    "display": [
                        {
                            "locale": "en",
                            "logo": {
                                "alt_text": "Blue Logo",
                                "uri": "https://example.com/images/logo.png",
                            },
                            "name": "Open Badge Credential",
                        }
                    ]
                },
                "credential_signing_alg_values_supported": ["ES256", "EdDSA"],
                "cryptographic_binding_methods_supported": [
                    "did:jwk",
                    "did:key",
                    "did:web",
                ],
                "format": "vc+sd-jwt",
                "proof_types_supported": {
                    "jwt": {"proof_signing_alg_values_supported": ["ES256", "EdDSA"]}
                },
            }
        )

        credential_configuration = msgspec.json.decode(
            supported_config_json, type=CredentialConfiguration
        )

        # When deserializing from credential issuer metadata, we don't have an
        # id, so it's an empty string, the default
        # That's the main difference.
        assert credential_configuration.credential_configuration_id == ""

        assert credential_configuration.format == "vc+sd-jwt"
        assert credential_configuration.credential_definition is not None
        assert credential_configuration.credential_definition.type == [
            "VerifiableCredential",
            "OpenBadgeCredential",
        ]
