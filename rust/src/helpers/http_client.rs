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

#[cfg(test)]
mod tests {
    use super::helpers::*;
    use super::HttpResponse;
    use std::collections::HashMap;

    // ─── HttpResponse::text() ────────────────────────────────────────

    #[test]
    fn test_response_text_empty() {
        let resp = HttpResponse {
            status_code: 200,
            url: "http://test".to_string(),
            headers: HashMap::new(),
            content: vec![],
        };
        assert_eq!(resp.text(), "");
    }

    #[test]
    fn test_response_text_utf8() {
        let body = b"Hello, world!";
        let resp = HttpResponse {
            status_code: 200,
            url: "http://test".to_string(),
            headers: HashMap::new(),
            content: body.to_vec(),
        };
        assert_eq!(resp.text(), "Hello, world!");
    }

    // ─── build_url ──────────────────────────────────────────────────

    #[test]
    fn test_build_url() {
        assert_eq!(build_url("http://localhost:8001", "/v0/offers"),
                   "http://localhost:8001/v0/offers");
    }

    #[test]
    fn test_build_url_single_segment() {
        assert_eq!(build_url("http://api.test", "/health"),
                   "http://api.test/health");
    }

    // ─── add_bearer_token ───────────────────────────────────────────

    #[test]
    fn test_add_bearer_token() {
        let mut headers = HashMap::new();
        add_bearer_token(&mut headers, "my-token-123");
        assert_eq!(headers.get("Authorization"),
                   Some(&"Bearer my-token-123".to_string()));
    }

    // ─── add_content_type_json ──────────────────────────────────────

    #[test]
    fn test_add_content_type_json() {
        let mut headers = HashMap::new();
        add_content_type_json(&mut headers);
        assert_eq!(headers.get("Content-Type"),
                   Some(&"application/json".to_string()));
    }

    // ─── is_success boundary tests ─────────────────────────────────

    #[test]
    fn test_is_success_199_fails() {
        assert!(!is_success(199));
    }

    #[test]
    fn test_is_success_200_succeeds() {
        assert!(is_success(200));
    }

    #[test]
    fn test_is_success_299_succeeds() {
        assert!(is_success(299));
    }

    #[test]
    fn test_is_success_300_fails() {
        assert!(!is_success(300));
    }

    // ─── is_error boundary tests ───────────────────────────────────

    #[test]
    fn test_is_error_399_fails() {
        assert!(!is_error(399));
    }

    #[test]
    fn test_is_error_400_succeeds() {
        assert!(is_error(400));
    }

    #[test]
    fn test_is_error_599_succeeds() {
        assert!(is_error(599));
    }

    #[test]
    fn test_is_error_600_fails() {
        assert!(!is_error(600));
    }

    // ─── build_error_body ──────────────────────────────────────────

    #[test]
    fn test_build_error_body() {
        let resp = HttpResponse {
            status_code: 503,
            url: "http://test".to_string(),
            headers: HashMap::new(),
            content: b"Service unavailable".to_vec(),
        };
        let body = build_error_body(503, &resp);
        assert!(body.contains("503"));
        assert!(body.contains("Service unavailable"));
    }
}
