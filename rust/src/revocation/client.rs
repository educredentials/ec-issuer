/// Revocation client.
use std::collections::HashMap;

use crate::helpers::http_client::helpers::{build_url, is_success};
use crate::helpers::http_client::{HttpClient, HttpClientError};

/// Revocation client for interacting with the vc-service.
pub struct RevocationClient<C: HttpClient> {
    client: C,
    base_url: String,
}

impl<C: HttpClient> RevocationClient<C> {
    /// Create a new revocation client.
    ///
    /// # Arguments
    ///
    /// * `client` - HTTP client implementation.
    /// * `base_url` - Base URL of the vc-service.
    pub fn new(client: C, base_url: impl Into<String>) -> Self {
        Self {
            client,
            base_url: base_url.into(),
        }
    }

    /// Revoke a credential by its credential status ID.
    ///
    /// # Arguments
    ///
    /// * `credential_status_id` - The credential status ID to revoke.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on network or revocation failures.
    pub fn revoke(
        &self,
        credential_status_id: &str,
        bearer_token: &str,
    ) -> Result<(), HttpClientError> {
        let url = build_url(
            &self.base_url,
            &format!("/credential-status/{credential_status_id}/revoke"),
        );

        let mut headers = HashMap::new();
        crate::helpers::http_client::helpers::add_bearer_token(&mut headers, bearer_token);

        let response = self.client.delete(&url, &headers)?;

        if is_success(response.status_code) {
            Ok(())
        } else {
            Err(HttpClientError::Http {
                status: response.status_code,
                body: crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            })
        }
    }

    /// Revoke a credential via the SSI agent API.
    ///
    /// # Arguments
    ///
    /// * `credential_id` - The credential ID to revoke.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on network or revocation failures.
    pub fn revoke_via_ssi_agent(&self, credential_id: &str) -> Result<(), HttpClientError> {
        let url = build_url(&self.base_url, &format!("/v0/credentials/{credential_id}"));

        let mut headers = HashMap::new();
        crate::helpers::http_client::helpers::add_content_type_json(&mut headers);

        let payload = r#"{"credentialStatus":"INVALID"}"#;

        let response = self.client.patch(&url, &headers, payload)?;

        if is_success(response.status_code) {
            Ok(())
        } else {
            Err(HttpClientError::Http {
                status: response.status_code,
                body: crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            })
        }
    }

    /// Suspend a credential by its credential status ID.
    ///
    /// # Arguments
    ///
    /// * `credential_status_id` - The credential status ID to suspend.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on network or revocation failures.
    pub fn suspend(
        &self,
        credential_status_id: &str,
        bearer_token: &str,
    ) -> Result<(), HttpClientError> {
        let url = build_url(
            &self.base_url,
            &format!("/credential-status/{credential_status_id}/suspend"),
        );

        let mut headers = HashMap::new();
        crate::helpers::http_client::helpers::add_bearer_token(&mut headers, bearer_token);

        let response = self.client.delete(&url, &headers)?;

        if is_success(response.status_code) {
            Ok(())
        } else {
            Err(HttpClientError::Http {
                status: response.status_code,
                body: crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            })
        }
    }
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::*;
    use crate::helpers::http_client::{HttpClientError, HttpResponse};

    struct TestClient {
        delete_status: Option<u16>,
        delete_body: Option<Vec<u8>>,
        patch_status: Option<u16>,
        patch_body: Option<Vec<u8>>,
    }

    impl TestClient {
        fn with_delete_ok(status: u16, body: &[u8]) -> Self {
            Self {
                delete_status: Some(status),
                delete_body: Some(body.to_vec()),
                patch_status: None,
                patch_body: None,
            }
        }

        fn with_delete_err() -> Self {
            Self {
                delete_status: None,
                delete_body: None,
                patch_status: None,
                patch_body: None,
            }
        }

        fn with_patch_ok(status: u16, body: &[u8]) -> Self {
            Self {
                delete_status: None,
                delete_body: None,
                patch_status: Some(status),
                patch_body: Some(body.to_vec()),
            }
        }

        fn with_patch_err() -> Self {
            Self {
                delete_status: None,
                delete_body: None,
                patch_status: None,
                patch_body: None,
            }
        }
    }

    impl HttpClient for TestClient {
        fn get(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn post(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn delete(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            match (self.delete_status, self.delete_body.as_ref()) {
                (Some(s), Some(b)) => Ok(HttpResponse {
                    status_code: s,
                    url: "http://mock".to_string(),
                    headers: HashMap::new(),
                    content: b.clone(),
                }),
                _ => Err(HttpClientError::Connection("not configured".to_string())),
            }
        }
        fn patch(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            match (self.patch_status, self.patch_body.as_ref()) {
                (Some(s), Some(b)) => Ok(HttpResponse {
                    status_code: s,
                    url: "http://mock".to_string(),
                    headers: HashMap::new(),
                    content: b.clone(),
                }),
                _ => Err(HttpClientError::Connection("not configured".to_string())),
            }
        }
    }

    #[test]
    fn test_revoke_returns_ok_on_success() {
        let mock = TestClient::with_delete_ok(200, b"{}");
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.revoke("status-id", "token");
        assert!(result.is_ok());
    }

    #[test]
    fn test_revoke_returns_error_on_failure() {
        let mock = TestClient::with_delete_ok(400, b"Bad request");
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.revoke("status-id", "token");
        assert!(result.is_err());
        match result.unwrap_err() {
            HttpClientError::Http { status: 400, .. } => {}
            other => panic!("expected HttpClientError::Http 400, got {other:?}"),
        }
    }

    #[test]
    fn test_revoke_returns_error_on_connection() {
        let mock = TestClient::with_delete_err();
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.revoke("status-id", "token");
        assert!(result.is_err());
    }

    #[test]
    fn test_revoke_via_ssi_agent_returns_ok_on_success() {
        let mock = TestClient::with_patch_ok(200, b"{}");
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.revoke_via_ssi_agent("cred-1");
        assert!(result.is_ok());
    }

    #[test]
    fn test_revoke_via_ssi_agent_returns_error_on_failure() {
        let mock = TestClient::with_patch_ok(400, b"Bad request");
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.revoke_via_ssi_agent("cred-1");
        assert!(result.is_err());
    }

    #[test]
    fn test_suspend_returns_ok_on_success() {
        let mock = TestClient::with_delete_ok(200, b"{}");
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.suspend("status-id", "token");
        assert!(result.is_ok());
    }

    #[test]
    fn test_suspend_returns_error_on_failure() {
        let mock = TestClient::with_delete_ok(400, b"Bad request");
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.suspend("status-id", "token");
        assert!(result.is_err());
    }

    #[test]
    fn test_suspend_returns_error_on_connection() {
        let mock = TestClient::with_delete_err();
        let client = RevocationClient::new(mock, "http://mock");
        let result = client.suspend("status-id", "token");
        assert!(result.is_err());
    }
}
