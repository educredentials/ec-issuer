use tracing::level_filters::LevelFilter;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

pub fn tracing_init() {
    let env_filter = EnvFilter::builder()
        .with_default_directive(LevelFilter::INFO.into())
        .from_env_lossy();

    tracing_subscriber::registry()
        .with(env_filter)
        .with(tracing_subscriber::fmt::layer())
        .init();
}
