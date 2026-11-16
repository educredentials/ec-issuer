/// Credential configurations bootstrap.
use crate::config::Config;
use crate::credential_configurations::models::CredentialConfiguration;

/// Bootstrap credential configurations from the SSI agent.
///
/// # Arguments
///
/// * `config` - Application configuration.
///
/// # Errors
///
/// Returns an error if the HTTP request to the SSI agent fails.
#[allow(clippy::unused_async)]
pub async fn bootstrap_credentials(
    config: &Config,
) -> Result<Vec<CredentialConfiguration>, Box<dyn std::error::Error + Send + Sync>> {
    let _url = format!("{}/credential-configurations", config.ssi_agent_url);
    // TODO: implement HTTP GET to SSI agent
    let resp: Vec<CredentialConfiguration> = Vec::new();
    Ok(resp)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_bootstrap_credentials_empty() {
        let env = vec![
            ("SERVER_HOST".to_string(), "0.0.0.0".to_string()),
            ("SERVER_PORT".to_string(), "8080".to_string()),
            ("SSI_AGENT_URL".to_string(), "http://localhost:8001".to_string()),
            ("AWARDS_SERVICE_URL".to_string(), "http://localhost:8002".to_string()),
            ("CREDENTIAL_CONVERTER_URL".to_string(), "http://localhost:8003".to_string()),
            ("DEBUG".to_string(), "false".to_string()),
            ("POSTGRES_CONNECTION_STRING".to_string(), "postgres://localhost/test".to_string()),
            ("ALLOWED_CORS_DOMAINS".to_string(), "*".to_string()),
        ];
        let config = Config::load(Some(env), None);
        let result = bootstrap_credentials(&config).await;
        assert!(result.is_ok());
        assert!(result.unwrap().is_empty());
    }
}
