//! HTTP route definitions

use axum::{
    routing::{get, post},
    Router,
};

use super::handlers::{
    get_credential, health_check, issue_credential, list_credentials, revoke_credential, AppState,
};

/// Create the router with all routes
pub fn create_router(state: AppState) -> Router {
    Router::new()
        // Health check
        .route("/health", get(health_check))
        // Credential operations
        .route("/api/v1/credentials", post(issue_credential))
        .route("/api/v1/credentials", get(list_credentials))
        .route("/api/v1/credentials/:id", get(get_credential))
        .route("/api/v1/credentials/:id/revoke", post(revoke_credential))
        .with_state(state)
}
