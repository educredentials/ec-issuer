/// Credential converter port.
use crate::helpers::http_client::HttpClientError;

/// Error raised when credential conversion fails.
#[derive(Debug, thiserror::Error)]
#[error("Credential converter error: {0}")]
pub struct CredentialConverterClientError(pub String);

impl From<HttpClientError> for CredentialConverterClientError {
    fn from(e: HttpClientError) -> Self {
        Self(e.to_string())
    }
}

/// Port: interface for converting credentials between formats.
pub trait CredentialConverterPort {
    /// Convert an OB3 credential to an EDC/ELM credential.
    ///
    /// Encodes the input as base64, POSTs to the converter service at
    /// `/api`, and decodes the base64-wrapped JSON response.
    ///
    /// # Arguments
    ///
    /// * `credential_json` - The OB3 credential as a JSON value.
    ///
    /// # Errors
    ///
    /// Returns `CredentialConverterClientError` on conversion failures.
    fn convert(
        &self,
        credential_json: &serde_json::Value,
    ) -> Result<serde_json::Value, CredentialConverterClientError>;
}
