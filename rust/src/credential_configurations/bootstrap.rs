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
