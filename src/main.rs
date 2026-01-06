//! Main Application Entry Point
//!
//! This is where hexagonal architecture comes together:
//! 1. Load configuration
//! 2. Initialize infrastructure adapters (outbound ports)
//! 3. Wire up application services (inbound ports)
//! 4. Start HTTP server (inbound adapter)

use credential_adapters::{
    AppState, GrpcSigningClient, InMemoryAchievementClient, InMemoryIssuerClient,
    InMemorySigningClient, PostgresCredentialRepository, StubEventPublisher,
};
use credential_ports::CredentialService;
use credential_serializers::{ELMSerializer, OB3Serializer};
use sqlx::postgres::PgPoolOptions;
use std::sync::Arc;
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod config;
use config::Config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "credential_service=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Starting Credential Service");

    // Load configuration
    let config = Config::from_env()?;
    tracing::info!("Configuration loaded");

    // Initialize database connection pool
    let pool = PgPoolOptions::new()
        .connect(&config.database.url)
        .await?;

    tracing::info!("Database connection established");

    // Run migrations
    let repository = PostgresCredentialRepository::new(pool);
    repository.migrate().await?;
    tracing::info!("Database migrations completed");

    // Initialize adapters (outbound ports)
    let repository = Arc::new(repository);

    let signing_client: Arc<dyn credential_ports::SigningClient> = if config.signing.use_grpc {
        Arc::new(GrpcSigningClient::new(config.signing.service_url.clone()))
    } else {
        Arc::new(InMemorySigningClient::new())
    };

    let achievement_client = Arc::new(InMemoryAchievementClient::new());
    let issuer_client = Arc::new(InMemoryIssuerClient::new());
    let event_publisher = Arc::new(StubEventPublisher::new());

    // Initialize serializers
    let serializers: Vec<Arc<dyn credential_ports::CredentialSerializer>> = vec![
        Arc::new(OB3Serializer::new()),
        Arc::new(ELMSerializer::new()),
    ];

    tracing::info!("Adapters initialized");

    // Create application service (implements use cases)
    let credential_service = Arc::new(CredentialService::new(
        repository.clone(),
        signing_client,
        achievement_client,
        issuer_client,
        event_publisher,
        serializers,
    ));

    tracing::info!("Application services initialized");

    // Create HTTP application state
    let app_state = AppState {
        issue_credential: credential_service.clone(),
        get_credential: credential_service.clone(),
        list_credentials: credential_service.clone(),
        revoke_credential: credential_service.clone(),
    };

    // Create router with all routes
    let app = credential_adapters::create_router(app_state)
        .layer(TraceLayer::new_for_http());

    // Start server
    let addr = format!("{}:{}", config.server.host, config.server.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;

    tracing::info!("Server listening on {}", addr);
    tracing::info!("Health check: http://{}/health", addr);
    tracing::info!("API base URL: http://{}/api/v1", addr);

    axum::serve(listener, app).await?;

    Ok(())
}
