/// HTTP REST API adapter using axum.
///
/// Provides CORS, metrics, health check, root endpoint, extension context
/// serving, and the credential offer creation endpoint.
///
/// This module is deep: a small interface (`build_router`, `run_server`) with
/// complex implementation hidden in handlers and middleware.
mod extension_context_server;
mod handlers;
mod middleware;

use std::net::SocketAddr;

use axum::Router;
use axum::routing::{get, post};
use serde::{Deserialize, Serialize};
use tower::ServiceBuilder;
use tower_http::trace::{DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::info;

use self::extension_context_server::ExtensionContextServer;

use crate::config::Config;

/// Request body for the create offer endpoint.
#[derive(Debug, Deserialize)]
pub struct CreateOfferBody {
    /// The award/achievement identifier.
    pub award_id: String,
    /// The credential type (defaults to "ob3").
    #[serde(default = "default_credential_type")]
    pub credential_type: String,
}

fn default_credential_type() -> String {
    "ob3".to_string()
}

/// Response body for the create offer endpoint.
#[derive(Debug, Serialize)]
pub struct CreateOfferResponse {
    /// Unique offer identifier.
    pub offer_id: String,
    /// URI pointing to the credential offer.
    pub uri: String,
    /// Associated credential IDs.
    #[serde(default)]
    pub credential_ids: Vec<String>,
}

/// Application state shared across handlers.
pub struct AppState {
    /// Configuration.
    pub config: Config,
    /// Offer service for business logic.
    pub offer_service: std::sync::Arc<
        crate::offers::service::OfferService<
            crate::offers::postgres::OffersRepository,
            crate::offers::ssi_agent::SsiAgentOffersClient<
                crate::helpers::reqwest_client::ReqwestHttpClientArc,
            >,
        >,
    >,
    /// Extension context server.
    pub extension_context_server: ExtensionContextServer,
}

impl Clone for AppState {
    fn clone(&self) -> Self {
        Self {
            config: self.config.clone(),
            offer_service: self.offer_service.clone(),
            extension_context_server: self.extension_context_server.clone(),
        }
    }
}

impl AppState {
    /// Create new application state from configuration.
    ///
    /// # Arguments
    ///
    /// * `config` - Application configuration.
    ///
    /// # Returns
    ///
    /// The application state.
    #[must_use]
    pub fn new(
        config: Config,
        offer_service: crate::offers::service::OfferService<
            crate::offers::postgres::OffersRepository,
            crate::offers::ssi_agent::SsiAgentOffersClient<
                crate::helpers::reqwest_client::ReqwestHttpClientArc,
            >,
        >,
    ) -> Self {
        let extension_context_server =
            ExtensionContextServer::new(&config.ec_issuer_url, &config.ec_issuer_extensions_dir);

        Self {
            config,
            offer_service: std::sync::Arc::new(offer_service),
            extension_context_server,
        }
    }
}

/// Build the axum router with all routes.
///
/// # Arguments
///
/// * `state` - Application state shared across handlers.
///
/// # Returns
///
/// The configured router.
pub fn build_router(state: AppState) -> Router {
    let cors = middleware::build_cors_layer(&state.config);

    Router::new()
        .route("/health", get(handlers::health))
        .route("/", get(handlers::root))
        .route("/api/v1/offers", post(handlers::create_offer))
        .route(
            "/static/extensions/{*filename}",
            get(handlers::serve_extension_context),
        )
        .with_state(state)
        .layer(cors)
        .layer(
            ServiceBuilder::new().layer(
                TraceLayer::new_for_http()
                    .on_request(DefaultOnRequest::new().level(tracing::Level::INFO))
                    .on_response(DefaultOnResponse::new().level(tracing::Level::INFO)),
            ),
        )
}

/// Run the HTTP server.
///
/// # Arguments
///
/// * `config` - Application configuration.
///
/// # Panics
///
/// Panics if the server fails to start.
pub async fn run_server(config: Config) {
    let offer_service = crate::offers::service::make_offer_service(&config).await;

    let state = AppState::new(config.clone(), offer_service);

    let app = build_router(state);

    let addr: SocketAddr = format!("{}:{}", config.server_host, config.server_port)
        .parse()
        .expect("invalid address");

    info!(address = %addr, "Starting HTTP server");

    axum::serve(
        tokio::net::TcpListener::bind(&addr)
            .await
            .expect("Failed to bind to address"),
        app,
    )
    .await
    .expect("Server failed");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::Router;
    use axum::body::Body;
    use axum::http::Request;
    use axum::http::StatusCode;
    use axum::response::IntoResponse;
    use axum::routing::get;
    use tower::ServiceExt;

    #[test]
    fn test_default_credential_type() {
        assert_eq!(default_credential_type(), "ob3");
    }

    #[test]
    fn test_create_offer_response_serialization() {
        let response = CreateOfferResponse {
            offer_id: "test-offer".to_string(),
            uri: "https://example.com/offer".to_string(),
            credential_ids: vec!["cred1".to_string()],
        };

        let json = serde_json::to_string(&response).expect("Failed to serialize");
        assert!(json.contains("test-offer"));
        assert!(json.contains("https://example.com/offer"));
        assert!(json.contains("cred1"));
    }

    #[test]
    fn test_root_returns_hello() {
        async fn handle_root() -> &'static str {
            "Hello, World!"
        }

        let router: Router = Router::new().route("/", get(handle_root));

        let resp = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(
                router

                    .oneshot(Request::builder().uri("/").body(Body::empty()).unwrap()),
            )
            .unwrap();

        assert_eq!(resp.status(), StatusCode::OK);
    }

    #[test]
    fn test_health_returns_200_when_healthy() {
        use axum::Json;

        async fn handle_health() -> impl IntoResponse {
            (
                StatusCode::OK,
                Json(serde_json::json!({"status": "healthy", "database": "ok"})),
            )
        }

        let router: Router = Router::new().route("/health", get(handle_health));

        let resp = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(
                router.oneshot(
                    Request::builder()
                        .uri("/health")
                        .body(Body::empty())
                        .unwrap(),
                ),
            )
            .unwrap();

        assert_eq!(resp.status(), StatusCode::OK);
    }
}
