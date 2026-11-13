/// Credential converter client.
use std::collections::HashMap;

use crate::helpers::http_client::helpers::{build_url, is_error};
use crate::helpers::http_client::{HttpClient, HttpResponse};
use base64::{Engine as _, engine::general_purpose::STANDARD};

use super::port::{CredentialConverterClientError, CredentialConverterPort};

/// Path the converter service listens on.
const CONVERSION_PATH: &str = "/api";
/// Preferred language for conversion.
const PREFERRED_LANGUAGE: &str = "en";

/// Credential converter client.
///
/// Encodes the input credential as base64, POSTs to the converter's `/api`
/// endpoint with a wrapped JSON payload, and decodes the base64-wrapped
/// response.
pub struct CredentialConverterClient<C: HttpClient> {
    /// Base URL of the credential converter service.
    base_url: String,
    /// HTTP client implementation.
    client: C,
}

impl<C: HttpClient> CredentialConverterClient<C> {
    /// Create a new credential converter client.
    ///
    /// # Arguments
    ///
    /// * `client` - HTTP client implementation.
    /// * `base_url` - Base URL of the credential converter service.
    pub fn new(client: C, base_url: &str) -> Self {
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            client,
        }
    }

    /// Execute the HTTP call to the converter.
    fn _do_convert(
        &self,
        credential: &serde_json::Value,
    ) -> Result<serde_json::Value, CredentialConverterClientError> {
        let content = self._encode_input(credential);
        let payload = self._build_request(&content);

        let response = self._http_post(&payload)?;
        self._decode_response(&response)
    }

    /// Base64-encode the input credential JSON.
    fn _encode_input(&self, credential: &serde_json::Value) -> String {
        STANDARD.encode(credential.to_string().as_bytes())
    }

    /// Build the converter request payload.
    fn _build_request(&self, content: &str) -> String {
        serde_json::to_string(&serde_json::json!({
            "From": {"Name": "OB", "Version": "3.0"},
            "To": {"Name": "elm", "Version": "3.2"},
            "Parameters": {"PreferredLanguages": [PREFERRED_LANGUAGE]},
            "Content": content,
        }))
        .expect("convert request is valid JSON")
    }

    /// POST to the converter's `/api` endpoint.
    fn _http_post(&self, body: &str) -> Result<HttpResponse, CredentialConverterClientError> {
        let url = build_url(&self.base_url, CONVERSION_PATH);
        let mut headers = HashMap::new();
        headers.insert("Content-Type".to_string(), "application/json".to_string());

        let response = self
            .client
            .post(&url, &headers, body)
            .map_err(|e| CredentialConverterClientError(e.to_string()))?;

        match response.status_code {
            400 => {
                let body = String::from_utf8_lossy(&response.content);
                return Err(CredentialConverterClientError(format!(
                    "Converter returned 400: {body}"
                )));
            }
            500..=599 => {
                let body = String::from_utf8_lossy(&response.content);
                return Err(CredentialConverterClientError(format!(
                    "Converter returned {}: {body}",
                    response.status_code
                )));
            }
            _ if !is_error(response.status_code) => (),
            _ => {
                let body = String::from_utf8_lossy(&response.content);
                return Err(CredentialConverterClientError(format!(
                    "Converter returned unexpected status {}: {body}",
                    response.status_code
                )));
            }
        }

        Ok(response)
    }

    /// Decode the converter response.
    fn _decode_response(
        &self,
        response: &HttpResponse,
    ) -> Result<serde_json::Value, CredentialConverterClientError> {
        let data: serde_json::Value = serde_json::from_slice(&response.content).map_err(|e| {
            CredentialConverterClientError(format!("Invalid JSON response from converter: {e}"))
        })?;

        if let Some(error_msg) = data.get("error").and_then(|v| v.as_str()) {
            let message = data.get("message").and_then(|v| v.as_str()).unwrap_or("");
            return Err(CredentialConverterClientError(format!(
                "Converter error: {error_msg} - {message}"
            )));
        }

        let content = data
            .get("content")
            .ok_or_else(|| {
                CredentialConverterClientError(
                    "Converter response missing 'content' field".to_string(),
                )
            })?
            .as_str()
            .ok_or_else(|| {
                CredentialConverterClientError(
                    "Converter response 'content' field is not a string".to_string(),
                )
            })?;

        let raw = STANDARD.decode(content).map_err(|e| {
            CredentialConverterClientError(format!(
                "Failed to base64-decode converter response: {e}"
            ))
        })?;

        serde_json::from_slice(&raw).map_err(|e| {
            CredentialConverterClientError(format!("Failed to decode converter response: {e}"))
        })
    }
}

impl<C: HttpClient> CredentialConverterPort for CredentialConverterClient<C> {
    fn convert(
        &self,
        credential_json: &serde_json::Value,
    ) -> Result<serde_json::Value, CredentialConverterClientError> {
        self._do_convert(credential_json)
    }
}

/// Convenience constructor for the Arc-wrapped client type.
#[must_use]
pub fn new_credential_converter_client_arc(
    client: &crate::helpers::reqwest_client::ReqwestHttpClientArc,
    base_url: &str,
) -> CredentialConverterClient<crate::helpers::reqwest_client::ReqwestHttpClientArc> {
    CredentialConverterClient::new(client.clone(), base_url)
}
