/// Credential issuer metadata models.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Image {
    pub uri: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub alt_text: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Display {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub locale: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub logo: Option<Image>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub background_color: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub background_image: Option<Image>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text_color: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct KeyAttestation {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub key_storage: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user_authentication: Option<Vec<String>>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ProofType {
    pub proof_signing_alg_values_supported: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub key_attestations_required: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CredentialTemplate {
    #[serde(rename = "format")]
    pub format: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub scope: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cryptographic_binding_methods_supported: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub credential_signing_alg_values_supported: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub proof_types_supported: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display: Option<Vec<Display>>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CredentialResponseEncryption {
    pub alg_values_supported: Vec<String>,
    pub enc_values_supported: Vec<String>,
    pub encryption_required: bool,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BatchCredentialIssuance {
    pub batch_size: i64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct CredentialIssuerMetadata {
    pub credential_issuer: String,
    pub credential_endpoint: String,
    pub credential_configurations_supported: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub authorization_servers: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub nonce_endpoint: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub deferred_credential_endpoint: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub notification_endpoint: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub credential_response_encryption: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub batch_credential_issuance: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display: Option<Vec<Display>>,
}

impl CredentialIssuerMetadata {
    pub fn authorization_server(&self) -> &str {
        match &self.authorization_servers {
            Some(servers) if !servers.is_empty() => &servers[0],
            _ => &self.credential_issuer,
        }
    }
}
