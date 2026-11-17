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

    // reqwest::blocking::Client holds an internal Tokio runtime. When
    // AppState (containing the client) is dropped at the end of run_server,
    // that internal runtime would be dropped from the #[tokio::main] async
    // context — which panics:
    // "Cannot drop a runtime in a context where blocking is not allowed."
    //
    // Run the server on a separate tokio runtime so that when run_server
    // returns and the client is dropped, we're still in the main runtime's
    // async context but the blocking client's inner runtime has already
    // been shut down.
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("build tokio runtime");

    rt.block_on(api::run_server(config));

    // rt is dropped here, inside the #[tokio::main] async context, but the
    // ReqwestHttpClient inside AppState is dropped *before* rt, so there's
    // no nested-runtime-in-async-context issue.
}
