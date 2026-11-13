/// Middleware: CORS layer builder and auth header extraction.
use http::HeaderValue;
use http::{HeaderMap, StatusCode};
use tower_http::cors::{Any, CorsLayer};

use crate::config::Config;

/// Build a CORS layer from configuration.
///
/// # Arguments
///
/// * `config` - Application configuration containing allowed CORS domains.
///
/// # Returns
///
/// A configured `CorsLayer`.
pub fn build_cors_layer(config: &Config) -> CorsLayer {
    if config.allowed_cors_domains == "*" {
        CorsLayer::new().allow_origin(Any)
    } else {
        let origins: Vec<HeaderValue> = config
            .allowed_cors_domains
            .split(',')
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .filter_map(|s| s.parse().ok())
            .collect();
        let origin_list = tower_http::cors::AllowOrigin::list(origins);
        CorsLayer::new().allow_origin(origin_list)
    }
}

/// Extract the bearer token from the Authorization header.
///
/// # Arguments
///
/// * `headers` - The request headers.
///
/// # Returns
///
/// `Ok(token)` when the header contains `Bearer <token>`.
/// `Err(status_code)` when the header is missing or malformed.
pub fn extract_bearer_token(headers: &HeaderMap) -> Result<String, StatusCode> {
    headers.get("Authorization").map_or(Err(StatusCode::UNAUTHORIZED), |auth_header| {
        let auth_str = auth_header.to_str().unwrap_or("");
        auth_str
            .strip_prefix("Bearer ")
            .map(str::to_string)
            .ok_or(StatusCode::UNAUTHORIZED)
    })
}

/// Map an offer service error string to an HTTP response.
///
/// # Arguments
///
/// * `error` - The error message from the offer service.
///
/// # Returns
///
/// A tuple of `(StatusCode, Json<Value>)`.
pub fn map_service_error(error: &str) -> (StatusCode, serde_json::Value) {
    if error.contains("not found") {
        (StatusCode::NOT_FOUND, serde_json::json!({"error": error}))
    } else if error.contains("Forbidden") || error.contains("Access denied") {
        (
            StatusCode::FORBIDDEN,
            serde_json::json!({"error": "Forbidden"}),
        )
    } else if error.contains("Unsupported credential_type") {
        (StatusCode::BAD_REQUEST, serde_json::json!({"error": error}))
    } else {
        (StatusCode::BAD_GATEWAY, serde_json::json!({"error": error}))
    }
}
