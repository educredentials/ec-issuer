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
    pub max_connections: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SigningConfig {
    pub use_grpc: bool,
    pub service_url: String,
}

impl Config {
    /// Load configuration from environment variables
    pub fn from_env() -> anyhow::Result<Self> {
        let server = ServerConfig {
            host: std::env::var("SERVER_HOST").unwrap_or_else(|_| "0.0.0.0".to_string()),
            port: std::env::var("SERVER_PORT")
                .unwrap_or_else(|_| "3000".to_string())
                .parse()?,
        };

        let database = DatabaseConfig {
            url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgresql://postgres:postgres@localhost/credentials".to_string()),
            max_connections: std::env::var("DATABASE_MAX_CONNECTIONS")
                .unwrap_or_else(|_| "5".to_string())
                .parse()?,
        };

        let signing = SigningConfig {
            use_grpc: std::env::var("SIGNING_USE_GRPC")
                .unwrap_or_else(|_| "false".to_string())
                .parse()?,
            service_url: std::env::var("SIGNING_SERVICE_URL")
                .unwrap_or_else(|_| "http://localhost:50051".to_string()),
        };

        Ok(Config {
            server,
            database,
            signing,
        })
    }
}
