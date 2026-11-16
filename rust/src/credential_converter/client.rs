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

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::*;
    use crate::helpers::http_client::{HttpClientError, HttpResponse};

    struct MockClient {
        post_status: Option<u16>,
        post_body: Option<Vec<u8>>,
        post_err: Option<String>,
    }

    impl MockClient {
        fn with_post_ok(status: u16, body: &[u8]) -> Self {
            Self {
                post_status: Some(status),
                post_body: Some(body.to_vec()),
                post_err: None,
            }
        }

        fn with_post_err(msg: &str) -> Self {
            Self {
                post_status: None,
                post_body: None,
                post_err: Some(msg.to_string()),
            }
        }
    }

    impl HttpClient for MockClient {
        fn get(&self, _url: &str, _headers: &HashMap<String, String>) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn post(&self, _url: &str, _headers: &HashMap<String, String>, _body: &str) -> Result<HttpResponse, HttpClientError> {
            if let Some(ref err) = self.post_err {
                return Err(HttpClientError::Connection(err.clone()));
            }
            match (self.post_status, self.post_body.as_ref()) {
                (Some(s), Some(b)) => Ok(HttpResponse {
                    status_code: s,
                    url: "http://mock/api".to_string(),
                    headers: HashMap::new(),
                    content: b.clone(),
                }),
                _ => Err(HttpClientError::Connection("not configured".to_string())),
            }
        }
        fn delete(&self, _url: &str, _headers: &HashMap<String, String>) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn patch(&self, _url: &str, _headers: &HashMap<String, String>, _body: &str) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
    }

    // ─── _encode_input tests ────────────────────────────────────────

    #[test]
    fn test_encode_input_returns_non_empty() {
        let cred = serde_json::json!({"type": "VerifiableCredential"});
        let mock = MockClient::with_post_ok(200, b"{}");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let encoded = client._encode_input(&cred);
        assert!(!encoded.is_empty());
        // Verify it's valid base64 by decoding
        let decoded = STANDARD.decode(&encoded).unwrap();
        assert_eq!(String::from_utf8_lossy(&decoded), cred.to_string());
    }

    #[test]
    fn test_encode_input_is_valid_base64() {
        let cred = serde_json::json!({"key": "value"});
        let mock = MockClient::with_post_ok(200, b"{}");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let encoded = client._encode_input(&cred);
        let decoded = STANDARD.decode(&encoded).unwrap();
        let decoded_json: serde_json::Value = serde_json::from_slice(&decoded).unwrap();
        assert_eq!(decoded_json, cred);
    }

    // ─── _build_request tests ───────────────────────────────────────

    #[test]
    fn test_build_request_produces_valid_json() {
        let mock = MockClient::with_post_ok(200, b"{}");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake-content");
        let parsed: serde_json::Value = serde_json::from_str(&payload).unwrap();
        assert_eq!(parsed["From"]["Name"], serde_json::json!("OB"));
        assert_eq!(parsed["From"]["Version"], serde_json::json!("3.0"));
        assert_eq!(parsed["To"]["Name"], serde_json::json!("elm"));
        assert_eq!(parsed["To"]["Version"], serde_json::json!("3.2"));
        assert_eq!(parsed["Parameters"]["PreferredLanguages"], serde_json::json!(["en"]));
        assert_eq!(parsed["Content"], serde_json::json!("fake-content"));
    }

    // ─── _http_post tests ───────────────────────────────────────────

    #[test]
    fn test_http_post_200_succeeds() {
        // Pre-computed base64 of {"type":["VerifiableCredential"],"name":"Test"}
        let good_cred = serde_json::json!({"type":["VerifiableCredential"],"name":"Test"});
        let encoded = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, good_cred.to_string().as_bytes());
        let response_body = serde_json::json!({"content": encoded});
        let mock = MockClient::with_post_ok(200, &response_body.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake-content");
        let result = client._http_post(&payload);
        assert!(result.is_ok());
    }

    #[test]
    fn test_http_post_400_returns_error_with_status() {
        let mock = MockClient::with_post_ok(400, b"Bad request body");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake-content");
        match client._http_post(&payload) {
            Err(CredentialConverterClientError(msg)) => {
                assert!(msg.starts_with("Converter returned 400: "));
            }
            Ok(_) => panic!("expected error on 400"),
        }
    }

    #[test]
    fn test_http_post_500_returns_error_with_status() {
        let mock = MockClient::with_post_ok(500, b"Internal server error");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake-content");
        match client._http_post(&payload) {
            Err(CredentialConverterClientError(msg)) => {
                assert!(msg.starts_with("Converter returned 500: "));
            }
            Ok(_) => panic!("expected error on 500"),
        }
    }

    #[test]
    fn test_http_post_404_falls_to_fallback_error() {
        // 404 is not 400, not 500..=599, and !is_error(404) is false
        // so it should hit the fallback error arm
        let mock = MockClient::with_post_ok(404, b"Not found");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake-content");
        match client._http_post(&payload) {
            Err(CredentialConverterClientError(msg)) => {
                assert!(msg.contains("404"));
                assert!(msg.contains("unexpected"));
            }
            Ok(_) => panic!("expected error on 404"),
        }
    }

    #[test]
    fn test_http_post_connection_error() {
        let mock = MockClient::with_post_err("connection refused");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake-content");
        match client._http_post(&payload) {
            Err(CredentialConverterClientError(_)) => {}
            Ok(_) => panic!("expected error"),
        }
    }

    // ─── _decode_response tests ─────────────────────────────────────

    #[test]
    fn test_decode_response_valid_json() {
        let good_cred = serde_json::json!({"type":["VerifiableCredential"],"name":"Test"});
        let encoded = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, good_cred.to_string().as_bytes());
        let response_body = serde_json::json!({"content": encoded});
        let mock = MockClient::with_post_ok(200, &response_body.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake");
        let response = client._http_post(&payload).unwrap();
        let result = client._decode_response(&response);
        assert!(result.is_ok());
        let decoded = result.unwrap();
        assert_eq!(decoded["type"], serde_json::json!(["VerifiableCredential"]));
        assert_eq!(decoded["name"], serde_json::json!("Test"));
    }

    #[test]
    fn test_decode_response_error_field() {
        let error_body = serde_json::json!({"error": "bad_request", "message": "invalid input"});
        let mock = MockClient::with_post_ok(200, &error_body.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake");
        let response = client._http_post(&payload).unwrap();
        match client._decode_response(&response) {
            Err(CredentialConverterClientError(msg)) => {
                assert!(msg.contains("Converter error"));
                assert!(msg.contains("bad_request"));
            }
            Ok(_) => panic!("expected error"),
        }
    }

    #[test]
    fn test_decode_response_missing_content() {
        let no_content = serde_json::json!({"other": "data"});
        let mock = MockClient::with_post_ok(200, &no_content.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake");
        let response = client._http_post(&payload).unwrap();
        match client._decode_response(&response) {
            Err(CredentialConverterClientError(msg)) => assert!(msg.contains("missing")),
            Ok(_) => panic!("expected error"),
        }
    }

    #[test]
    fn test_decode_response_non_string_content() {
        let not_string = serde_json::json!({"content": 123});
        let mock = MockClient::with_post_ok(200, &not_string.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let payload = client._build_request("fake");
        let response = client._http_post(&payload).unwrap();
        match client._decode_response(&response) {
            Err(CredentialConverterClientError(msg)) => assert!(msg.contains("not a string")),
            Ok(_) => panic!("expected error"),
        }
    }

    // ─── Full pipeline tests ────────────────────────────────────────

    #[test]
    fn test_convert_returns_valid_json() {
        let valid_cred = serde_json::json!({"type": "VerifiableCredential", "name": "Test"});
        let encoded = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, valid_cred.to_string().as_bytes());
        let response_body = serde_json::json!({"content": encoded});
        let mock = MockClient::with_post_ok(200, &response_body.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let input = serde_json::json!({"from": "ob3"});
        let result = client.convert(&input);
        assert!(result.is_ok());
        let decoded = result.unwrap();
        assert_eq!(decoded["type"], serde_json::json!("VerifiableCredential"));
    }

    #[test]
    fn test_convert_fails_on_bad_400() {
        let mock = MockClient::with_post_ok(400, b"Bad request");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let input = serde_json::json!({"from": "ob3"});
        match client.convert(&input) {
            Err(CredentialConverterClientError(msg)) => assert!(msg.contains("400")),
            Ok(_) => panic!("expected error"),
        }
    }

    #[test]
    fn test_convert_fails_on_bad_500() {
        let mock = MockClient::with_post_ok(500, b"Internal server error");
        let client = CredentialConverterClient::new(mock, "http://mock");
        let input = serde_json::json!({"from": "ob3"});
        match client.convert(&input) {
            Err(CredentialConverterClientError(msg)) => assert!(msg.contains("500")),
            Ok(_) => panic!("expected error"),
        }
    }

    #[test]
    fn test_do_convert_returns_correct_value() {
        let valid_cred = serde_json::json!({"result": "converted"});
        let encoded = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, valid_cred.to_string().as_bytes());
        let response_body = serde_json::json!({"content": encoded});
        let mock = MockClient::with_post_ok(200, &response_body.to_string().into_bytes());
        let client = CredentialConverterClient::new(mock, "http://mock");
        let result = client._do_convert(&serde_json::json!({}));
        assert!(result.is_ok());
        let decoded = result.unwrap();
        assert_eq!(decoded["result"], serde_json::json!("converted"));
    }
}
