/// SSI agent credential configurations client.
use std::collections::HashMap;

use crate::helpers::http_client::helpers::{build_url, parse_json};
use crate::helpers::http_client::{HttpClient, HttpClientError};

/// Client for credential configurations on the SSI agent.
pub struct SsiAgentCredentialConfigurationsClient<C: HttpClient> {
    client: C,
    base_url: String,
}

impl<C: HttpClient> SsiAgentCredentialConfigurationsClient<C> {
    /// Create a new SSI agent credential configurations client.
    ///
    /// # Arguments
    ///
    /// * `client` - HTTP client implementation.
    /// * `base_url` - Base URL of the SSI agent.
    pub fn new(client: C, base_url: &str) -> Self {
        Self {
            client,
            base_url: base_url.trim_end_matches('/').to_string(),
        }
    }

    /// Get a credential configuration by ID from the SSI agent.
    ///
    /// # Arguments
    ///
    /// * `config_id` - Credential configuration ID.
    ///
    /// # Returns
    ///
    /// The credential configuration.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on network errors, or when the ID is
    /// absent from the listing.
    pub fn get(&self, config_id: &str) -> Result<serde_json::Value, HttpClientError> {
        // The SSI agent has no per-ID endpoint; the Python adapter
        // retrieves from the listing and filters client-side.
        let all = self.list()?;
        all.into_iter()
            .find(|t| t.get("id").and_then(serde_json::Value::as_str) == Some(config_id))
            .ok_or_else(|| {
                HttpClientError::Connection(format!("Credential template not found: {config_id}"))
            })
    }

    /// Create a new credential configuration.
    ///
    /// # Arguments
    ///
    /// * `config` - The credential configuration JSON object.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP or serialization failure.
    ///
    /// # Returns
    ///
    /// The created configuration as JSON.
    pub fn create(&self, config: &serde_json::Value) -> Result<serde_json::Value, HttpClientError> {
        let url = build_url(&self.base_url, "/v0/create-new-template");

        let mut headers = HashMap::new();
        headers.insert("Content-Type".to_string(), "application/json".to_string());

        let body = self
            .client
            .post(&url, &headers, &serde_json::to_string(config)?)?;
        parse_json(&body)
    }

    /// List all credential configurations.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    ///
    /// # Returns
    ///
    /// A list of credential configurations as JSON.
    pub fn list(&self) -> Result<Vec<serde_json::Value>, HttpClientError> {
        let url = build_url(&self.base_url, "/v0/list-all-templates");

        let body = self.client.get(&url, &HashMap::new())?;
        parse_json(&body)
    }

    /// Delete a credential configuration by ID.
    ///
    /// # Arguments
    ///
    /// * `config_id` - The credential configuration ID to delete.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    pub fn delete(&self, config_id: &str) -> Result<(), HttpClientError> {
        let url = build_url(&self.base_url, "/v0/templates/delete-template");

        let mut headers = HashMap::new();
        headers.insert("Content-Type".to_string(), "application/json".to_string());

        let payload = serde_json::json!({"templateId": config_id});
        let _body = self
            .client
            .post(&url, &headers, &serde_json::to_string(&payload)?)?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::*;
    use crate::helpers::http_client::{HttpClientError, HttpResponse};

    struct MockClient {
        get_status: Option<u16>,
        get_body: Option<Vec<u8>>,
        get_err: Option<String>,
        post_status: Option<u16>,
        post_body: Option<Vec<u8>>,
        post_err: Option<String>,
    }

    impl MockClient {
        fn with_get_ok(status: u16, body: &[u8]) -> Self {
            Self {
                get_status: Some(status),
                get_body: Some(body.to_vec()),
                get_err: None,
                post_status: None,
                post_body: None,
                post_err: None,
            }
        }

        fn with_post_ok(status: u16, body: &[u8]) -> Self {
            Self {
                get_status: None,
                get_body: None,
                get_err: None,
                post_status: Some(status),
                post_body: Some(body.to_vec()),
                post_err: None,
            }
        }

        fn with_get_err(msg: &str) -> Self {
            Self {
                get_status: None,
                get_body: None,
                get_err: Some(msg.to_string()),
                post_status: None,
                post_body: None,
                post_err: None,
            }
        }

        fn with_post_err(msg: &str) -> Self {
            Self {
                get_status: None,
                get_body: None,
                get_err: None,
                post_status: None,
                post_body: None,
                post_err: Some(msg.to_string()),
            }
        }
    }

    impl HttpClient for MockClient {
        fn get(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            if let Some(ref err) = self.get_err {
                return Err(HttpClientError::Connection(err.clone()));
            }
            match (self.get_status, self.get_body.as_ref()) {
                (Some(s), Some(b)) => Ok(HttpResponse {
                    status_code: s,
                    url: "http://mock".to_string(),
                    headers: HashMap::new(),
                    content: b.clone(),
                }),
                _ => Err(HttpClientError::Connection("not configured".to_string())),
            }
        }

        fn post(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            if let Some(ref err) = self.post_err {
                return Err(HttpClientError::Connection(err.clone()));
            }
            match (self.post_status, self.post_body.as_ref()) {
                (Some(s), Some(b)) => Ok(HttpResponse {
                    status_code: s,
                    url: "http://mock".to_string(),
                    headers: HashMap::new(),
                    content: b.clone(),
                }),
                _ => Err(HttpClientError::Connection("not configured".to_string())),
            }
        }

        fn delete(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }

        fn patch(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
    }

    #[test]
    fn test_create_returns_ok() {
        let mock = MockClient::with_post_ok(200, b"{}");
        let client = SsiAgentCredentialConfigurationsClient::new(mock, "http://mock");
        let config =
            serde_json::json!({"id": "cfg-1", "type": ["VerifiedCertificate"], "name": "Test"});
        let result = client.create(&config);
        assert!(result.is_ok());
    }

    #[test]
    fn test_create_returns_error_on_network_fail() {
        let mock = MockClient::with_post_err("connection refused");
        let client = SsiAgentCredentialConfigurationsClient::new(mock, "http://mock");
        let config = serde_json::json!({"id": "cfg-1"});
        let result = client.create(&config);
        assert!(result.is_err());
    }

    #[test]
    fn test_list_returns_ok() {
        let body = b"[{\"id\":\"cfg-1\"}]";
        let mock = MockClient::with_get_ok(200, body);
        let client = SsiAgentCredentialConfigurationsClient::new(mock, "http://mock");
        let result = client.list();
        assert!(result.is_ok());
        let configs = result.unwrap();
        assert_eq!(configs.len(), 1);
    }

    #[test]
    fn test_get_returns_ok() {
        let body = b"[{\"id\":\"cfg-1\",\"type\":[\"VerifiedCertificate\"],\"name\":\"Test\"}]";
        let mock = MockClient::with_get_ok(200, body);
        let client = SsiAgentCredentialConfigurationsClient::new(mock, "http://mock");
        let result = client.get("cfg-1").unwrap();
        assert_eq!(result["id"], "cfg-1");
    }

    #[test]
    fn test_get_returns_error_when_id_absent() {
        let body = b"[{\"id\":\"cfg-1\"}]";
        let mock = MockClient::with_get_ok(200, body);
        let client = SsiAgentCredentialConfigurationsClient::new(mock, "http://mock");
        let result = client.get("missing");
        assert!(result.is_err());
    }

    #[test]
    fn test_get_returns_error_on_network_fail() {
        let mock = MockClient::with_get_err("connection refused");
        let client = SsiAgentCredentialConfigurationsClient::new(mock, "http://mock");
        let result = client.get("cfg-1");
        assert!(result.is_err());
    }
}
