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

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::*;
    use crate::helpers::http_client::{HttpClientError, HttpResponse};

    struct MockClient {
        get_status: Option<u16>,
        get_body: Option<Vec<u8>>,
        get_err: Option<String>,
    }

    impl MockClient {
        fn with_get_ok(status: u16, body: &[u8]) -> Self {
            Self {
                get_status: Some(status),
                get_body: Some(body.to_vec()),
                get_err: None,
            }
        }

        fn with_get_err(msg: &str) -> Self {
            Self {
                get_status: None,
                get_body: None,
                get_err: Some(msg.to_string()),
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
        fn post(&self, _url: &str, _headers: &HashMap<String, String>, _body: &str) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn delete(&self, _url: &str, _headers: &HashMap<String, String>) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn patch(&self, _url: &str, _headers: &HashMap<String, String>, _body: &str) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
    }

    #[test]
    fn test_fetch_and_decode_returns_non_empty() {
        let body = r#"{"key": "value"}"#;
        let mock = MockClient::with_get_ok(200, body.as_bytes());
        let client = HttpAwardsClient::new("http://mock", "http://issuer", mock);
        let result = client._fetch_and_decode("award-1", "token");
        assert!(result.is_ok());
        let map = result.unwrap();
        assert_eq!(map.len(), 1);
        assert!(map.contains_key("key"));
    }

    #[test]
    fn test_fetch_and_decode_404() {
        let mock = MockClient::with_get_ok(404, b"Not found");
        let client = HttpAwardsClient::new("http://mock", "http://issuer", mock);
        let result = client._fetch_and_decode("award-1", "token");
        assert!(result.is_err());
        match result.unwrap_err() {
            AwardError::NotFound(_) => {}
            other => panic!("expected NotFound, got {other:?}"),
        }
    }

    #[test]
    fn test_fetch_and_decode_403() {
        let mock = MockClient::with_get_ok(403, b"Forbidden");
        let client = HttpAwardsClient::new("http://mock", "http://issuer", mock);
        let result = client._fetch_and_decode("award-1", "token");
        assert!(result.is_err());
        match result.unwrap_err() {
            AwardError::Forbidden(_) => {}
            other => panic!("expected Forbidden, got {other:?}"),
        }
    }

    #[test]
    fn test_fetch_and_decode_connection_error() {
        let mock = MockClient::with_get_err("connection refused");
        let client = HttpAwardsClient::new("http://mock", "http://issuer", mock);
        let result = client._fetch_and_decode("award-1", "token");
        assert!(result.is_err());
    }
}
