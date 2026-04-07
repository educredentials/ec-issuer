"""Unit tests for metadata module."""

import msgspec
import pytest

from src.metadata.metadata import CredentialConfiguration, CredentialIssuerMetadata


class TestDeserializeMetadata:
    """
    Test that metadata object tree can be deserialized from JSON.
    """

    def test_deserialize_metadata_simple_valid(self):
        json = b"""
        {
            "credential_issuer": "https://issuer.example.com",
            "credential_endpoint": "https://issuer.example.com/credential",
            "authorization_servers": ["https://authn.example.com"],
            "credential_configurations_supported": {}
        }"""

        metadata: CredentialIssuerMetadata = msgspec.json.decode(
            json, type=CredentialIssuerMetadata
        )
        assert metadata.credential_issuer == "https://issuer.example.com"

    def test_deserialize_metadata_extended_valid(self):
        json = b"""
        {
          "credential_issuer": "https://issuer.example.com",
          "credential_endpoint": "https://issuer.example.com/credential",
          "authorization_servers": ["https://authn.example.com"],
          "display": [
             {
               "name": "UniversityIssuer",
               "logo": {
                 "uri": "https://university.example.edu/public/logo.png",
                 "alt_text": "a square logo of a university"
               },
               "locale": "en-US",
               "background_color": "#12107c",
               "text_color": "#FFFFFF"
             }
           ],
          "credential_configurations_supported": {
            "SD_JWT_VC_example_in_OpenID4VCI": {
              "format": "dc+sd-jwt",
              "scope": "SD_JWT_VC_example_in_OpenID4VCI",
              "cryptographic_binding_methods_supported": [
                "jwk"
              ],
              "credential_signing_alg_values_supported": [
                "ES256"
              ],
              "display": [
                {
                  "name": "IdentityCredential",
                  "logo": {
                    "uri": "https://university.example.edu/public/logo.png",
                    "alt_text": "a square logo of a university"
                  },
                  "locale": "en-US",
                  "background_color": "#12107c",
                  "text_color": "#FFFFFF"
                }
              ],
              "proof_types_supported": {
                "jwt": {
                  "proof_signing_alg_values_supported": [
                    "ES256"
                  ]
                }
              },
              "vct": "SD_JWT_VC_example_in_OpenID4VCI",
              "claims": [
                {
                  "path": ["given_name"],
                  "display": [
                    {
                      "name": "Given Name",
                      "locale": "en-US"
                    },
                    {
                      "name": "Vorname",
                      "locale": "de-DE"
                    }
                  ]
                },
                {
                  "path": ["family_name"],
                  "display": [
                    {
                      "name": "Surname",
                      "locale": "en-US"
                    },
                    {
                      "name": "Nachname",
                      "locale": "de-DE"
                    }
                  ]
                },
                {"path": ["email"]},
                {"path": ["phone_number"]},
                {
                  "path": ["address"],
                  "display": [
                    {
                      "name": "Place of residence",
                      "locale": "en-US"
                    },
                    {
                      "name": "Wohnsitz",
                      "locale": "de-DE"
                    }
                  ]
                },
                {"path": ["address", "street_address"]},
                {"path": ["address", "locality"]},
                {"path": ["address", "region"]},
                {"path": ["address", "country"]},
                {"path": ["birthdate"]},
                {"path": ["is_over_18"]},
                {"path": ["is_over_21"]},
                {"path": ["is_over_65"]}
              ]
            }
          }
        }"""

        metadata: CredentialIssuerMetadata = msgspec.json.decode(
            json, type=CredentialIssuerMetadata
        )
        config = metadata.credential_configurations_supported.get(
            "SD_JWT_VC_example_in_OpenID4VCI"
        )

        assert isinstance(config, CredentialConfiguration)

        ## Decend into an arbitrary but deep nested structure as smoke test
        proof_types = config.proof_types_supported
        assert proof_types is not None
        jwt = proof_types.get("jwt")
        assert jwt is not None
        assert jwt.proof_signing_alg_values_supported == ["ES256"]

    def test_deserialize_metadata_invalid(self):
        with pytest.raises(
            msgspec.DecodeError,
            match="Object missing required field `credential_issuer`",
        ):
            _ = msgspec.json.decode(b"{}", type=CredentialIssuerMetadata)
