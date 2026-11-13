/// Web server binary for the Educredentials Issuer.
///
/// This binary starts the HTTP API server with CORS, health check,
/// extension context serving, and credential offer creation endpoints.
use ec_issuer::api;
use tracing::info;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    info!("Starting web server");

    let config = ec_issuer::config::Config::load(None, None);

    api::run_server(config).await;
}
