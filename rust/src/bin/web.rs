/// Web server binary for the Educredentials Issuer.
///
/// This binary starts the HTTP API server with CORS, health check,
/// extension context serving, and credential offer creation endpoints.
use ec_issuer::api;
use ec_issuer::helpers::reqwest_client::ReqwestHttpClientArc;
use tracing::info;

fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    info!("Starting web server");

    let config = ec_issuer::config::Config::load(None, None);

    // reqwest::blocking::Client spawns an internal Tokio runtime, and both
    // creating and dropping that runtime panics inside an async context
    // ("Cannot drop a runtime in a context where blocking is not allowed").
    // The client is therefore built here in sync main() and handed to the
    // server, so no blocking client is ever created or dropped within
    // run_server's async context.
    let http_client = ReqwestHttpClientArc::new();

    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .expect("build tokio runtime");

    rt.block_on(api::run_server(config, http_client));
}
