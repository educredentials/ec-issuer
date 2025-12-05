//! HTTP error handling

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use credential_domain::DomainError;
use serde_json::json;

/// Convert domain errors to HTTP responses
pub struct ApiError(pub DomainError);

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, error_message) = match &self.0 {
            DomainError::ValidationError { field, message } => (
                StatusCode::BAD_REQUEST,
                json!({
                    "error": "ValidationError",
                    "field": field,
                    "message": message
                }),
            ),
            DomainError::CredentialNotFound { id } => (
                StatusCode::NOT_FOUND,
                json!({
                    "error": "CredentialNotFound",
                    "id": id,
                    "message": format!("Credential not found: {}", id)
                }),
            ),
            DomainError::CredentialAlreadyRevoked { id } => (
                StatusCode::CONFLICT,
                json!({
                    "error": "CredentialAlreadyRevoked",
                    "id": id,
                    "message": format!("Credential already revoked: {}", id)
                }),
            ),
            DomainError::CredentialExpired { id } => (
                StatusCode::GONE,
                json!({
                    "error": "CredentialExpired",
                    "id": id,
                    "message": format!("Credential expired: {}", id)
                }),
            ),
            DomainError::InvalidCredentialStatus { status } => (
                StatusCode::BAD_REQUEST,
                json!({
                    "error": "InvalidCredentialStatus",
                    "status": status,
                    "message": format!("Invalid credential status: {}", status)
                }),
            ),
            DomainError::AchievementNotFound { id } => (
                StatusCode::NOT_FOUND,
                json!({
                    "error": "AchievementNotFound",
                    "id": id,
                    "message": format!("Achievement not found: {}", id)
                }),
            ),
            DomainError::IssuerNotFound { id } => (
                StatusCode::NOT_FOUND,
                json!({
                    "error": "IssuerNotFound",
                    "id": id,
                    "message": format!("Issuer not found: {}", id)
                }),
            ),
            DomainError::InvalidFormat { format } => (
                StatusCode::BAD_REQUEST,
                json!({
                    "error": "InvalidFormat",
                    "format": format,
                    "message": format!("Invalid format: {}", format)
                }),
            ),
            DomainError::SigningFailed { reason } => (
                StatusCode::INTERNAL_SERVER_ERROR,
                json!({
                    "error": "SigningFailed",
                    "message": reason
                }),
            ),
            DomainError::SerializationError { message } => (
                StatusCode::INTERNAL_SERVER_ERROR,
                json!({
                    "error": "SerializationError",
                    "message": message
                }),
            ),
        };

        (status, Json(error_message)).into_response()
    }
}

impl From<DomainError> for ApiError {
    fn from(err: DomainError) -> Self {
        ApiError(err)
    }
}
