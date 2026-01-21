use axum::{routing::get, Router};

mod logging;

mod config;
use config::Config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    logging::tracing_init();

    tracing::info!("Starting Credential Service");

    let config = Config::from_env()?;
    tracing::info!("Configuration loaded");

    let app = Router::new()
        .route("/", get(|| async { "Hello, world!" }))
        .route("/health", get(|| async { "OK" }));

    let addr = format!("{}:{}", config.server.host, config.server.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;

    tracing::info!("Server listening on {}", addr);

    axum::serve(listener, app).await?;

    Ok(())
}
