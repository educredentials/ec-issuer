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
        Self { client, base_url: base_url.into() }
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
            &format!("/credential-status/{credential_status_id}/revoke")
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
        let url = build_url(
            &self.base_url,
            &format!("/v0/credentials/{credential_id}")
        );

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
            &format!("/credential-status/{credential_status_id}/suspend")
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
