use tracing::level_filters::LevelFilter;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

/// Adapter: Logging trait that defines the interface for logging adapters
pub trait LoggerAdapter: Send + Sync {
    fn init(&self);
}

/// Text Adapter: Logs to stdout in text format
#[cfg(feature = "logging-text")]
pub struct TextLogger;

#[cfg(feature = "logging-text")]
impl LoggerAdapter for TextLogger {
    fn init(&self) {
        let env_filter = EnvFilter::builder()
            .with_default_directive(LevelFilter::INFO.into())
            .from_env_lossy();

        tracing_subscriber::registry()
            .with(env_filter)
            .with(tracing_subscriber::fmt::layer())
            .init();
    }
}

/// JSON Adapter: Logs to stdout in JSON format
#[cfg(feature = "logging-json")]
pub struct JsonLogger;

#[cfg(feature = "logging-json")]
impl LoggerAdapter for JsonLogger {
    fn init(&self) {
        let env_filter = EnvFilter::builder()
            .with_default_directive(LevelFilter::INFO.into())
            .from_env_lossy();

        tracing_subscriber::registry()
            .with(env_filter)
            .with(tracing_subscriber::fmt::layer().json())
            .init();
    }
}

/// Factory function to create the appropriate logger based on feature flags
pub fn create_logger() -> Box<dyn LoggerAdapter> {
    #[cfg(feature = "logging-text")]
    return Box::new(TextLogger);

    #[cfg(feature = "logging-json")]
    return Box::new(JsonLogger);
}

/// Initialize logging using the selected adapter
pub fn init_logging() {
    let logger = create_logger();
    logger.init();
}
