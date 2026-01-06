//! Configuration Management
//!
//! Loads configuration from environment variables or config files

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub signing: SigningConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SigningConfig {
    pub use_grpc: bool,
    pub service_url: String,
}

impl Config {
    /// Load configuration from environment variables
    /// Returns an error if any required environment variable is missing
    pub fn from_env() -> anyhow::Result<Self> {
        let server = ServerConfig {
            host: std::env::var("SERVER_HOST")?,
            port: std::env::var("SERVER_PORT")?.parse()?,
        };

        let database = DatabaseConfig {
            url: std::env::var("DATABASE_URL")?,
        };

        let signing = SigningConfig {
            use_grpc: std::env::var("SIGNING_USE_GRPC")?.parse()?,
            service_url: std::env::var("SIGNING_SERVICE_URL")?,
        };

        Ok(Config {
            server,
            database,
            signing,
        })
    }
}
