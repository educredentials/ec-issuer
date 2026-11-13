use axum::Json;
/// Handlers for HTTP endpoints.
use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;

use super::middleware::{extract_bearer_token, map_service_error};
use super::{AppState, CreateOfferBody, CreateOfferResponse};
use crate::offers::service::OfferServiceError;

/// Health check endpoint.
///
/// Returns 200 with DB status when healthy, or 503 when the
/// database is unreachable.
pub async fn health(State(state): State<AppState>) -> impl IntoResponse {
    let db_ok = state.offer_service.health_check().await;
    if db_ok {
        (
            StatusCode::OK,
            Json(serde_json::json!({
                "status": "healthy",
                "database": "ok"
            })),
        )
    } else {
        (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(serde_json::json!({
                "status": "unhealthy",
                "database": "error"
            })),
        )
    }
}

/// Root endpoint.
pub async fn root() -> &'static str {
    "Hello, World!"
}

/// Serve JSON-LD extension contexts from static/extensions/v1/.
///
/// SSI agents dereference these @context URLs when validating
/// credentials.  Only files under the configured extensions
/// directory are served.  The v1/ subdirectory holds versioned
/// extension context and schema files.
pub async fn serve_extension_context(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> impl IntoResponse {
    let (content, status_code, content_type) = state.extension_context_server.serve(&filename);

    let status = match status_code {
        200 => StatusCode::OK,
        _ => StatusCode::NOT_FOUND,
    };

    match content_type {
        Some(ct) => (status, [(axum::http::header::CONTENT_TYPE, ct)], content).into_response(),
        None => (status, content).into_response(),
    }
}

/// Create a credential offer for an achievement.
pub async fn create_offer(
    State(state): State<AppState>,
    headers: http::HeaderMap,
    Json(body): Json<CreateOfferBody>,
) -> impl IntoResponse {
    let bearer_token = match extract_bearer_token(&headers) {
        Ok(token) => token,
        Err(status) => {
            return (status, Json(serde_json::json!({"error": "Unauthorized"})));
        }
    };

    let credential_type = match crate::offers::models::CredentialType::from_short(&body.credential_type) {
        Ok(ct) => ct,
        Err(msg) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(serde_json::json!({"error": msg})),
            );
        }
    };
    let credential_type = match credential_type {
        crate::offers::models::CredentialType::OB3 => "ob3",
        crate::offers::models::CredentialType::EDC => "edc",
    };

    let result = state
        .offer_service
        .create_offer(&body.award_id, &bearer_token, credential_type)
        .await;

    match result {
        Ok(offer) => {
            let response = CreateOfferResponse {
                offer_id: offer.offer_id,
                uri: offer.uri.unwrap_or_default(),
                credential_ids: offer.credential_ids,
            };
            let json_body = serde_json::to_value(&response).unwrap_or_default();
            (StatusCode::CREATED, Json(json_body))
        }
        Err(OfferServiceError(e)) => {
            let (status, error_json) = map_service_error(&e);
            (status, Json(error_json))
        }
    }
}
