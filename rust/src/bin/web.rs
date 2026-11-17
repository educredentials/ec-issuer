/// Web server binary for the Educredentials Issuer.
///
/// This binary starts the HTTP API server with CORS, health check,
/// extension context serving, and credential offer creation endpoints.
use ec_issuer::api;
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

    // reqwest::blocking::Client holds an internal Tokio runtime. When
    // AppState (containing the ReqwestHttpClient) is dropped at the end of
    // run_server, that internal runtime is also dropped. If we used
    // #[tokio::main] the drop would happen from inside an async context —
    // triggering the panic:
    // "Cannot drop a runtime in a context where blocking is not allowed."
    //
    // By creating the runtime manually here (in sync main()), running the
    // server, and then dropping the runtime at the end of main(), the drop
    // happens in a sync context where blocking is allowed.
    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .expect("build tokio runtime");

    rt.block_on(api::run_server(config));
}
