//! HTTP request handlers

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    Json,
};
use credential_domain::CredentialFormat;
use credential_ports::*;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use super::errors::ApiError;

/// Application state shared across handlers
#[derive(Clone)]
pub struct AppState {
    pub issue_credential: Arc<dyn IssueCredentialUseCase>,
    pub get_credential: Arc<dyn GetCredentialUseCase>,
    pub list_credentials: Arc<dyn ListCredentialsUseCase>,
    pub revoke_credential: Arc<dyn RevokeCredentialUseCase>,
}

/// Issue a new credential
#[axum::debug_handler]
pub async fn issue_credential(
    State(state): State<AppState>,
    Json(request): Json<IssueCredentialRequest>,
) -> Result<(StatusCode, Json<IssueCredentialResponse>), ApiError> {
    let response = state.issue_credential.execute(request).await?;
    Ok((StatusCode::CREATED, Json(response)))
}

/// Get a credential by ID with optional format
#[derive(Debug, Deserialize)]
pub struct GetCredentialQuery {
    pub format: Option<String>,
}

#[axum::debug_handler]
pub async fn get_credential(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    Query(query): Query<GetCredentialQuery>,
) -> Result<Json<serde_json::Value>, ApiError> {
    let format = if let Some(format_str) = query.format {
        Some(format_str.parse::<CredentialFormat>()?)
    } else {
        None
    };

    let request = GetCredentialRequest { id, format };
    let response = state.get_credential.execute(request).await?;

    // Return formatted version if requested, otherwise canonical
    let result = if let Some(formatted) = response.formatted {
        formatted
    } else {
        serde_json::to_value(&response.credential)
            .map_err(|e| credential_domain::DomainError::serialization_error(e.to_string()))?
    };

    Ok(Json(result))
}

/// List credentials with filters
#[derive(Debug, Deserialize)]
pub struct ListCredentialsQuery {
    pub subject_id: Option<String>,
    pub issuer_id: Option<String>,
    pub achievement_id: Option<String>,
    pub status: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

#[derive(Debug, Serialize)]
pub struct ListCredentialsApiResponse {
    pub credentials: Vec<serde_json::Value>,
    pub total: i64,
}

#[axum::debug_handler]
pub async fn list_credentials(
    State(state): State<AppState>,
    Query(query): Query<ListCredentialsQuery>,
) -> Result<Json<ListCredentialsApiResponse>, ApiError> {
    let request = ListCredentialsRequest {
        subject_id: query.subject_id,
        issuer_id: query.issuer_id,
        achievement_id: query.achievement_id,
        status: query.status,
        limit: query.limit,
        offset: query.offset,
    };

    let response = state.list_credentials.execute(request).await?;

    let credentials: Result<Vec<serde_json::Value>, _> = response
        .credentials
        .iter()
        .map(|c| serde_json::to_value(c))
        .collect();

    let credentials = credentials
        .map_err(|e| credential_domain::DomainError::serialization_error(e.to_string()))?;

    Ok(Json(ListCredentialsApiResponse {
        credentials,
        total: response.total,
    }))
}

/// Revoke a credential
#[axum::debug_handler]
pub async fn revoke_credential(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    Json(request): Json<RevokeCredentialRequest>,
) -> Result<Json<RevokeCredentialResponse>, ApiError> {
    let mut request = request;
    request.id = id;

    let response = state.revoke_credential.execute(request).await?;
    Ok(Json(response))
}

/// Health check endpoint
pub async fn health_check() -> StatusCode {
    StatusCode::OK
}
