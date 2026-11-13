/// Configuration management using environment variables.
use crate::offers::models::CredentialType;

/// Configuration repository using environment variables.
#[derive(Clone)]
pub struct Config {
    /// Server host address.
    pub server_host: String,
    /// Server port number.
    pub server_port: u16,
    /// SSI agent base URL.
    pub ssi_agent_url: String,
    /// Awards service base URL.
    pub awards_service_url: String,
    /// Debug mode flag.
    pub debug: bool,
    /// PostgreSQL connection string.
    pub postgresql_connection_string: String,
    /// Allowed CORS domains (comma-separated or "*").
    pub allowed_cors_domains: String,
    /// EC issuer base URL.
    pub ec_issuer_url: String,
    /// Directory containing extension context JSON files.
    pub ec_issuer_extensions_dir: String,
    /// Credential configuration IDs keyed by type.
    pub credential_configuration_ids: std::collections::HashMap<CredentialType, String>,
    /// Credential converter service URL.
    pub credential_converter_url: String,
}

impl Config {
    /// Load configuration from environment variables.
    ///
    /// # Arguments
    ///
    /// * `env` - Optional override for `std::env::vars()`. Defaults to actual
    ///   environment if `None`.
    /// * `credential_configuration_ids` - Pre-resolved credential template IDs.
    ///
    /// # Panics
    ///
    /// Panics if required environment variables are missing.
    #[must_use]
    pub fn load(
        env: Option<Vec<(String, String)>>,
        credential_configuration_ids: Option<std::collections::HashMap<CredentialType, String>>,
    ) -> Self {
        let env = env.unwrap_or_else(|| std::env::vars().collect());
        let env_map: std::collections::HashMap<&str, &str> =
            env.iter().map(|(k, v)| (k.as_str(), v.as_str())).collect();

        Self {
            server_host: env_map
                .get("SERVER_HOST")
                .copied()
                .unwrap_or_else(|| panic!("SERVER_HOST not set"))
                .to_string(),
            server_port: env_map
                .get("SERVER_PORT")
                .copied()
                .map(|v| v.parse::<u16>().expect("SERVER_PORT must be a valid u16"))
                .expect("SERVER_PORT not set"),
            ssi_agent_url: env_map
                .get("SSI_AGENT_URL")
                .copied()
                .unwrap_or_else(|| panic!("SSI_AGENT_URL not set"))
                .to_string(),
            awards_service_url: env_map
                .get("AWARDS_SERVICE_URL")
                .copied()
                .unwrap_or_else(|| panic!("AWARDS_SERVICE_URL not set"))
                .to_string(),
            credential_converter_url: env_map
                .get("CREDENTIAL_CONVERTER_URL")
                .copied()
                .unwrap_or_else(|| panic!("CREDENTIAL_CONVERTER_URL not set"))
                .to_string(),
            debug: env_map
                .get("DEBUG")
                .copied()
                .is_some_and(|v| matches!(v, "true" | "1" | "yes")),
            postgresql_connection_string: env_map
                .get("POSTGRES_CONNECTION_STRING")
                .copied()
                .unwrap_or_else(|| panic!("POSTGRES_CONNECTION_STRING not set"))
                .to_string(),
            allowed_cors_domains: env_map
                .get("ALLOWED_CORS_DOMAINS")
                .copied()
                .unwrap_or_else(|| panic!("ALLOWED_CORS_DOMAINS not set"))
                .to_string(),
            ec_issuer_url: env_map
                .get("EC_ISSUER_URL")
                .copied()
                .unwrap_or("http://localhost:8000")
                .to_string(),
            ec_issuer_extensions_dir: env_map
                .get("EC_ISSUER_EXTENSIONS_DIR")
                .copied()
                .unwrap_or("/static/extensions")
                .to_string(),
            credential_configuration_ids: credential_configuration_ids.unwrap_or_default(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_load_from_map() {
        let env = vec![
            ("SERVER_HOST".to_string(), "0.0.0.0".to_string()),
            ("SERVER_PORT".to_string(), "8080".to_string()),
            (
                "SSI_AGENT_URL".to_string(),
                "http://localhost:8001".to_string(),
            ),
            (
                "AWARDS_SERVICE_URL".to_string(),
                "http://localhost:8002".to_string(),
            ),
            (
                "CREDENTIAL_CONVERTER_URL".to_string(),
                "http://localhost:8003".to_string(),
            ),
            (
                "POSTGRES_CONNECTION_STRING".to_string(),
                "postgres://localhost/test".to_string(),
            ),
            ("ALLOWED_CORS_DOMAINS".to_string(), "*".to_string()),
            ("DEBUG".to_string(), "true".to_string()),
        ];

        let config = Config::load(Some(env), None);

        assert_eq!(config.server_host, "0.0.0.0");
        assert_eq!(config.server_port, 8080);
        assert_eq!(config.ssi_agent_url, "http://localhost:8001");
        assert_eq!(config.awards_service_url, "http://localhost:8002");
        assert_eq!(config.credential_converter_url, "http://localhost:8003");
        assert_eq!(
            config.postgresql_connection_string,
            "postgres://localhost/test"
        );
        assert_eq!(config.allowed_cors_domains, "*");
        assert!(config.debug);
        assert_eq!(config.ec_issuer_url, "http://localhost:8000");
        assert_eq!(config.ec_issuer_extensions_dir, "/static/extensions");
    }

    #[test]
    fn test_config_defaults() {
        let env = vec![
            ("SERVER_HOST".to_string(), "0.0.0.0".to_string()),
            ("SERVER_PORT".to_string(), "8080".to_string()),
            (
                "SSI_AGENT_URL".to_string(),
                "http://localhost:8001".to_string(),
            ),
            (
                "AWARDS_SERVICE_URL".to_string(),
                "http://localhost:8002".to_string(),
            ),
            (
                "CREDENTIAL_CONVERTER_URL".to_string(),
                "http://localhost:8003".to_string(),
            ),
            (
                "POSTGRES_CONNECTION_STRING".to_string(),
                "postgres://localhost/test".to_string(),
            ),
            ("ALLOWED_CORS_DOMAINS".to_string(), "*".to_string()),
        ];

        let config = Config::load(Some(env), None);

        assert!(!config.debug);
        assert_eq!(config.ec_issuer_url, "http://localhost:8000");
        assert_eq!(config.ec_issuer_extensions_dir, "/static/extensions");
    }

    #[test]
    #[should_panic(expected = "SERVER_HOST not set")]
    fn test_config_missing_required_var_panics() {
        let env: Vec<(String, String)> = vec![];
        let _config = Config::load(Some(env), None);
    }
}
