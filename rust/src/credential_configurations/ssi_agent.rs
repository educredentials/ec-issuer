/// SSI agent credential configurations client.
use std::collections::HashMap;

use crate::credential_configurations::models::CredentialConfiguration;
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
    /// Returns `HttpClientError` on network errors.
    pub fn get(&self, config_id: &str) -> Result<CredentialConfiguration, HttpClientError> {
        let url = build_url(
            &self.base_url,
            &format!("/credential-configurations/{config_id}"),
        );

        let mut headers = HashMap::new();
        headers.insert("Accept".to_string(), "application/json".to_string());

        let body = self.client.get(&url, &headers)?;
        parse_json(&body)
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
