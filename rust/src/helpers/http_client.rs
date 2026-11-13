/// HTTP client trait for external services.
use std::collections::HashMap;

/// Trait for making HTTP requests to external services.
pub trait HttpClient {
    /// Send a GET request.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError::Http`, `HttpClientError::Connection`, or
    /// `HttpClientError::Timeout` on failure.
    fn get(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
    ) -> Result<HttpResponse, HttpClientError>;

    /// Send a POST request.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError::Http`, `HttpClientError::Connection`, or
    /// `HttpClientError::Timeout` on failure.
    fn post(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
        body: &str,
    ) -> Result<HttpResponse, HttpClientError>;

    /// Send a DELETE request.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError::Http`, `HttpClientError::Connection`, or
    /// `HttpClientError::Timeout` on failure.
    fn delete(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
    ) -> Result<HttpResponse, HttpClientError>;

    /// Send a PATCH request.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError::Http`, `HttpClientError::Connection`, or
    /// `HttpClientError::Timeout` on failure.
    fn patch(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
        body: &str,
    ) -> Result<HttpResponse, HttpClientError>;
}

/// HTTP response.
pub struct HttpResponse {
    /// HTTP status code.
    pub status_code: u16,
    /// Response URL.
    pub url: String,
    /// Response headers.
    pub headers: HashMap<String, String>,
    /// Response body as bytes.
    pub content: Vec<u8>,
}

impl HttpResponse {
    /// Get the response body as a string.
    #[must_use]
    pub fn text(&self) -> String {
        String::from_utf8_lossy(&self.content).to_string()
    }
}

impl From<serde_json::Error> for HttpClientError {
    fn from(e: serde_json::Error) -> Self {
        Self::Serialization(e.to_string())
    }
}

/// HTTP client error.
#[derive(Debug, thiserror::Error)]
pub enum HttpClientError {
    #[error("HTTP error: status={status}, body={body}")]
    Http { status: u16, body: String },
    #[error("Connection error: {0}")]
    Connection(String),
    #[error("Timeout")]
    Timeout,
    #[error("Serialization error: {0}")]
    Serialization(String),
}

/// Shared HTTP helpers used by all adapter clients.
///
/// This module is deep: a small interface of utility functions
/// that eliminate duplication across the awards, offers,
/// `credential_converter`, and revocation adapters.
pub mod helpers {
    use std::collections::HashMap;

    use super::{HttpClientError, HttpResponse};

    /// Build a full URL from base path and endpoint.
    ///
    /// # Arguments
    ///
    /// * `base` - Base URL (e.g. `http://localhost:8001`).
    /// * `path` - Endpoint path (e.g. `/v0/offers`).
    ///
    /// # Returns
    ///
    /// The full URL.
    #[must_use]
    pub fn build_url(base: &str, path: &str) -> String {
        format!("{base}{path}")
    }

    /// Add a Bearer token to the header map.
    #[allow(clippy::implicit_hasher)]
    pub fn add_bearer_token(headers: &mut HashMap<String, String>, token: &str) {
        headers.insert("Authorization".to_string(), format!("Bearer {token}"));
    }

    /// Add `Content-Type: application/json` to the header map.
    #[allow(clippy::implicit_hasher)]
    pub fn add_content_type_json(headers: &mut HashMap<String, String>) {
        headers.insert("Content-Type".to_string(), "application/json".to_string());
    }

    /// Return true for 2xx status codes.
    #[must_use]
    pub const fn is_success(status: u16) -> bool {
        status >= 200 && status < 300
    }

    /// Return true for 4xx or 5xx status codes.
    #[must_use]
    pub const fn is_error(status: u16) -> bool {
        status >= 400 && status < 600
    }

    /// Build an error body string from a response.
    #[must_use]
    pub fn build_error_body(status: u16, response: &HttpResponse) -> String {
        format!(
            "Upstream error: {} - {}",
            status,
            String::from_utf8_lossy(&response.content)
        )
    }

    /// Parse JSON from the response body.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError::Http` with a serialization detail if the
    /// response body is not valid JSON.
    pub fn parse_json<T: serde::de::DeserializeOwned>(
        response: &HttpResponse,
    ) -> Result<T, HttpClientError> {
        serde_json::from_slice(&response.content).map_err(|e| HttpClientError::Http {
            status: response.status_code,
            body: format!("Invalid response: {e}"),
        })
    }
}
