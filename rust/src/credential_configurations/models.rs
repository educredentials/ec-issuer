/// Credential configuration models.
use serde::{Deserialize, Serialize};

/// Credential configuration as returned by the SSI agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialConfiguration {
    /// Credential configuration ID.
    pub id: String,
    /// Credential type.
    pub r#type: Vec<String>,
    /// Credential name.
    pub name: String,
}

/// Logo display information.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Logo {
    /// Logo image URI.
    pub uri: String,
    /// Alt text for the logo.
    pub alt_text: String,
}

/// Display information for a credential configuration.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Display {
    /// Display name.
    pub name: String,
    /// Optional logo.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub logo: Option<Logo>,
}

/// Credential template for creating configurations.
///
/// Matches the Python `CredentialTemplate` dataclass, supporting both the
/// `OpenID4VCI` credential issuer metadata format and custom OBv3-specific
/// metadata (dataModel, holderType, etc.).
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CredentialTemplate {
    /// Credential template ID.
    #[serde(default)]
    pub id: String,
    /// Template title.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    /// Credential type.
    pub r#type: Vec<String>,
    /// Optional display information.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display: Option<Display>,
    /// Credential data model (e.g. "open_badges_3-0", "european_learning_model_v3-3").
    #[serde(rename = "dataModel", skip_serializing_if = "Option::is_none")]
    pub data_model: Option<String>,
    /// Template creator.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub creator: Option<String>,
    /// Holder type.
    #[serde(rename = "holderType", skip_serializing_if = "Option::is_none")]
    pub holder_type: Option<String>,
    /// Template tags.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tags: Option<Vec<String>>,
    /// Template status.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    /// Template visibility.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub visibility: Option<String>,
    /// Template description.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    /// Template schema.
    #[serde(default, skip_serializing_if = "is_empty")]
    pub schema: serde_json::Value,
}

/// Return true if the value is an empty JSON object `{}`.
fn is_empty(val: &serde_json::Value) -> bool {
    matches!(val, serde_json::Value::Object(map) if map.is_empty())
}
