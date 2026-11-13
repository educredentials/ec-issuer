/// HTTP awards client adapter.
use std::collections::HashMap;

use crate::awards::badgr_mapping::{AwardMappingError, ob3_award_from_badgr_api_response};
use crate::awards::models::OB3Award;
use crate::helpers::http_client::HttpClient;
use crate::helpers::http_client::helpers::{build_url, is_error, parse_json};

/// Error raised when an award is not found.
#[derive(Debug, thiserror::Error)]
#[error("Award not found: {0}")]
pub struct AwardNotFound(pub String);

/// Error raised when access to an award is forbidden.
#[derive(Debug, thiserror::Error)]
#[error("Award forbidden: {0}")]
pub struct AwardForbidden(pub String);

/// Error raised when the awards client encounters an error.
#[derive(Debug, thiserror::Error)]
#[error("Awards client error: {0}")]
pub struct AwardsClientError(pub String);

impl From<crate::helpers::http_client::HttpClientError> for AwardsClientError {
    fn from(e: crate::helpers::http_client::HttpClientError) -> Self {
        match e {
            crate::helpers::http_client::HttpClientError::Http { status, body } => {
                Self(format!("HTTP {status}: {body}"))
            }
            crate::helpers::http_client::HttpClientError::Connection(msg)
            | crate::helpers::http_client::HttpClientError::Serialization(msg) => Self(msg),
            crate::helpers::http_client::HttpClientError::Timeout => Self("Timeout".to_string()),
        }
    }
}

/// HTTP adapter for the awards service.
pub struct HttpAwardsClient<C: HttpClient> {
    awards_service_base_url: String,
    issuer_base_url: String,
    client: C,
}

impl<C: HttpClient> HttpAwardsClient<C> {
    /// Create a new HTTP awards client.
    ///
    /// # Arguments
    ///
    /// * `awards_service_url` - Base URL of the awards service.
    /// * `issuer_base_url` - Base URL for the issuer (for resolving relative paths).
    /// * `client` - HTTP client implementation.
    pub fn new(awards_service_url: &str, issuer_base_url: &str, client: C) -> Self {
        Self {
            awards_service_base_url: awards_service_url.trim_end_matches('/').to_string(),
            issuer_base_url: issuer_base_url.trim_end_matches('/').to_string(),
            client,
        }
    }

    /// Fetch and convert an award to an OB3 `AchievementCredential`.
    ///
    /// # Arguments
    ///
    /// * `award_id` - The unique award identifier.
    /// * `bearer_token` - The caller's bearer token for authentication.
    ///
    /// # Returns
    ///
    /// The matching OB3 Award.
    ///
    /// # Errors
    ///
    /// Returns `AwardNotFound` on 404, `AwardForbidden` on 403,
    /// `AwardsClientError` on other errors or invalid response.
    pub fn get_ob3(&self, award_id: &str, bearer_token: &str) -> Result<OB3Award, AwardError> {
        let raw = self._fetch_and_decode(award_id, bearer_token)?;

        let award_base_url = self.awards_service_base_url.clone();

        let raw_value = serde_json::to_value(&raw)
            .map_err(|e| AwardError::ClientError(AwardsClientError(format!("Failed to serialize award: {e}"))))?;

        let ob3 = ob3_award_from_badgr_api_response(
            &raw_value,
            Some(&award_base_url),
            Some(&self.issuer_base_url),
            Some("/static/extensions/v1"),
        )?;

        Ok(ob3)
    }

    fn _fetch_and_decode(
        &self,
        award_id: &str,
        bearer_token: &str,
    ) -> Result<HashMap<String, serde_json::Value>, AwardError> {
        let url = build_url(
            &self.awards_service_base_url,
            &format!("/awards/{award_id}"),
        );

        let mut headers = HashMap::new();
        crate::helpers::http_client::helpers::add_bearer_token(&mut headers, bearer_token);

        let response = self.client.get(&url, &headers)?;

        if response.status_code == 404 {
            return Err(AwardError::NotFound(AwardNotFound(format!(
                "Award {award_id} not found"
            ))));
        }

        if response.status_code == 403 {
            return Err(AwardError::Forbidden(AwardForbidden(format!(
                "Access to award {award_id} denied"
            ))));
        }

        if is_error(response.status_code) {
            return Err(AwardError::ClientError(AwardsClientError(
                crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            )));
        }

        let body = parse_json::<HashMap<String, serde_json::Value>>(&response)?;

        Ok(body)
    }
}

/// Unified award error type.
#[derive(Debug, thiserror::Error)]
pub enum AwardError {
    #[error(transparent)]
    NotFound(#[from] AwardNotFound),
    #[error(transparent)]
    Forbidden(#[from] AwardForbidden),
    #[error(transparent)]
    ClientError(#[from] AwardsClientError),
    #[error(transparent)]
    MappingError(#[from] AwardMappingError),
}

impl From<crate::helpers::http_client::HttpClientError> for AwardError {
    fn from(e: crate::helpers::http_client::HttpClientError) -> Self {
        Self::ClientError(AwardsClientError::from(e))
    }
}

/// Convenience constructor for the Arc-wrapped client type.
///
/// Returns `HttpAwardsClient<ReqwestHttpClientArc>` for use with axum's
/// `'static` state requirements.
#[must_use]
pub fn new_http_awards_client_arc(
    awards_service_url: &str,
    issuer_base_url: &str,
    client: &crate::helpers::reqwest_client::ReqwestHttpClientArc,
) -> HttpAwardsClient<crate::helpers::reqwest_client::ReqwestHttpClientArc> {
    HttpAwardsClient::new(awards_service_url, issuer_base_url, client.clone())
}
