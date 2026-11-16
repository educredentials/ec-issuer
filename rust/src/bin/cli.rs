/// CLI binary for the Educredentials Issuer.
///
/// Provides sysadmin commands for managing credential configurations and revoking credentials.
use std::io::Read;

use ec_issuer::config::Config;
use ec_issuer::credential_configurations::ssi_agent::SsiAgentCredentialConfigurationsClient;
use ec_issuer::helpers::http_client::HttpClient;
use ec_issuer::helpers::reqwest_client::ReqwestHttpClient;
use ec_issuer::revocation::client::RevocationClient;

/// Parsed CLI command routed from argument matching.
#[non_exhaustive]
#[derive(Debug, PartialEq, Eq)]
pub enum CommandRoute {
    /// `credential-configuration create <id>` — reads JSON from stdin.
    CreateCredentialConfiguration,
    /// `credential-configuration show <id>` — show by ID.
    ShowCredentialConfiguration(String),
    /// `credential-configuration update <id>` — reads JSON from stdin.
    UpdateCredentialConfiguration,
    /// `credential-configuration delete <id>` — delete by ID.
    DeleteCredentialConfiguration(String),
    /// `credential-configuration list` — list all.
    ListCredentialConfigurations,
    /// `revoke <id>` — revoke a credential.
    RevokeCredential(String),
    /// Unrecognised or incomplete credential-configuration arguments — print credential-config usage.
    ShowCredentialConfigUsage,
    /// Completely unknown command — print general usage.
    ShowUsage,
}

/// Route CLI argument slices to a [`CommandRoute`].
///
/// This function is pure and testable — it performs no I/O.
#[must_use]
pub fn route_command(args: &[&str]) -> CommandRoute {
    match args {
        ["credential-configuration", "create", _] => CommandRoute::CreateCredentialConfiguration,
        ["credential-configuration", "show", config_id] => {
            CommandRoute::ShowCredentialConfiguration(config_id.to_string())
        }
        ["credential-configuration", "update", _] => CommandRoute::UpdateCredentialConfiguration,
        ["credential-configuration", "delete", config_id] => {
            CommandRoute::DeleteCredentialConfiguration(config_id.to_string())
        }
        ["credential-configuration", "list"] => CommandRoute::ListCredentialConfigurations,
        [] | ["credential-configuration"] | ["credential-configuration", ..] => {
            CommandRoute::ShowCredentialConfigUsage
        }
        ["revoke", credential_id] => {
            CommandRoute::RevokeCredential(credential_id.to_string())
        }
        _ => CommandRoute::ShowUsage,
    }
}

const USAGE: &str = "\
Usage: ec-issuer <command> [args]

Commands:
    credential-configuration  - Manage credential configurations
    revoke <id>               - Revoke an issued credential by ID
";

const CREDENTIAL_CONFIG_USAGE: &str = "\
Usage: ec-issuer credential-configuration <command> [args]

Commands:
    create <id> - Create a new config (reads JSON from stdin)
    show <id>   - Show a credential configuration by ID
    update <id> - Update a config (reads JSON from stdin)
    delete <id> - Delete a credential configuration by ID
    list        - List all credential configurations
";

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let args_ref: Vec<&str> = args.iter().map(String::as_str).collect();

    let config = Config::load(None, None);

    let config_client = SsiAgentCredentialConfigurationsClient::new(
        ReqwestHttpClient::new(),
        &config.ssi_agent_url,
    );
    let revocation_client =
        RevocationClient::new(ReqwestHttpClient::new(), &config.ssi_agent_url);

    match execute(args_ref.as_slice(), &config_client, &revocation_client) {
        Ok(()) => {}
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}

/// Execute a CLI command with the given clients.
///
/// # Errors
///
/// Returns `Err` with an error message when the command fails:
/// - `ShowCredentialConfigUsage` or `ShowUsage` routes return descriptive messages.
/// - `handle_create` returns stdin read or JSON parse errors, or the client's error.
/// - `handle_show` returns the client's error (direct or fallback list lookup).
/// - `handle_list` returns the client's list error.
/// - `handle_delete` returns the client's error.
/// - `handle_revoke` returns the client's error.
///
/// This function is testable — it delegates to handler functions and returns results
/// instead of calling `process::exit`.
pub fn execute<C: HttpClient>(
    args: &[&str],
    config_client: &SsiAgentCredentialConfigurationsClient<C>,
    revocation_client: &RevocationClient<C>,
) -> Result<(), String> {
    match route_command(args) {
        CommandRoute::CreateCredentialConfiguration
        | CommandRoute::UpdateCredentialConfiguration => handle_create(config_client),
        CommandRoute::ShowCredentialConfiguration(config_id) => {
            handle_show(config_client, &config_id)
        }
        CommandRoute::DeleteCredentialConfiguration(config_id) => {
            handle_delete(config_client, &config_id)
        }
        CommandRoute::ListCredentialConfigurations => handle_list(config_client),
        CommandRoute::ShowCredentialConfigUsage => {
            eprintln!("{CREDENTIAL_CONFIG_USAGE}");
            Err("Missing arguments".to_string())
        }
        CommandRoute::ShowUsage => {
            eprintln!("{USAGE}");
            Err("Unknown command".to_string())
        }
        CommandRoute::RevokeCredential(credential_id) => {
            handle_revoke(revocation_client, &credential_id)
        }
    }
}

fn handle_create<C: HttpClient>(
    client: &SsiAgentCredentialConfigurationsClient<C>,
) -> Result<(), String> {
    let mut input = String::new();
    std::io::stdin()
        .read_to_string(&mut input)
        .map_err(|e| format!("Failed to read stdin: {e}"))?;

    let config: serde_json::Value =
        serde_json::from_str(&input).map_err(|e| format!("Invalid JSON: {e}"))?;

    let result = client.create(&config).map_err(|e| format!("{e}"))?;
    println!("{}", serde_json::to_string(&result).unwrap());
    Ok(())
}

fn handle_show<C: HttpClient>(
    client: &SsiAgentCredentialConfigurationsClient<C>,
    config_id: &str,
) -> Result<(), String> {
    match client.get(config_id) {
        Ok(config) => {
            println!("{}", serde_json::to_string(&config).unwrap());
            Ok(())
        }
        Err(ec_issuer::helpers::http_client::HttpClientError::Http { status: 0, .. }) => {
            // Try list-based lookup
            let templates = client.list().map_err(|e| format!("{e}"))?;
            for template in templates {
                if let Some(id) = template.get("id").and_then(|v| v.as_str()) {
                    if id == config_id {
                        println!("{}", serde_json::to_string(&template).unwrap());
                        return Ok(());
                    }
                }
            }
            Err(format!("Configuration not found: {config_id}"))
        }
        Err(e) => Err(format!("{e}")),
    }
}

fn handle_list<C: HttpClient>(
    client: &SsiAgentCredentialConfigurationsClient<C>,
) -> Result<(), String> {
    let templates = client.list().map_err(|e| format!("{e}"))?;
    println!("{}", serde_json::to_string(&templates).unwrap());
    Ok(())
}

fn handle_delete<C: HttpClient>(
    client: &SsiAgentCredentialConfigurationsClient<C>,
    config_id: &str,
) -> Result<(), String> {
    client.delete(config_id).map_err(|e| format!("{e}"))?;
    println!("Configuration \"{config_id}\" deleted");
    Ok(())
}

fn handle_revoke<C: HttpClient>(
    client: &RevocationClient<C>,
    credential_id: &str,
) -> Result<(), String> {
    client.revoke_via_ssi_agent(credential_id).map_err(|e| format!("{e}"))?;
    println!("Credential \"{credential_id}\" revoked");
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use ec_issuer::helpers::http_client::{HttpClientError, HttpResponse};

    use super::*;

    // ─── Mock HTTP clients ─────────────────────────────────────────────

    /// A mock HTTP client for testing CLI handlers.
    struct MockClient {
        get_responses: Vec<(Option<u16>, Option<Vec<u8>>, Option<String>)>,
        post_responses: Vec<(Option<u16>, Option<Vec<u8>>, Option<String>)>,
        patch_responses: Vec<(Option<u16>, Option<Vec<u8>>, Option<String>)>,
        call_count: std::cell::Cell<usize>,
    }

    impl MockClient {
        fn new() -> Self {
            Self {
                get_responses: vec![],
                post_responses: vec![],
                patch_responses: vec![],
                call_count: std::cell::Cell::new(0),
            }
        }

        fn add_get_response(self, status: Option<u16>, body: Option<&[u8]>, err: Option<&str>) -> Self {
            Self {
                get_responses: {
                    let mut r = self.get_responses;
                    r.push((status, body.map(|b| b.to_vec()), err.map(String::from)));
                    r
                },
                ..self
            }
        }

        fn add_post_response(self, status: Option<u16>, body: Option<&[u8]>, err: Option<&str>) -> Self {
            Self {
                post_responses: {
                    let mut r = self.post_responses;
                    r.push((status, body.map(|b| b.to_vec()), err.map(String::from)));
                    r
                },
                ..self
            }
        }

        fn add_patch_response(self, status: Option<u16>, body: Option<&[u8]>, err: Option<&str>) -> Self {
            Self {
                patch_responses: {
                    let mut r = self.patch_responses;
                    r.push((status, body.map(|b| b.to_vec()), err.map(String::from)));
                    r
                },
                ..self
            }
        }

        /// Convenience: configure first GET to return status+body, second to return list JSON.
        fn with_fallback_list(
            self,
            first_status: u16,
            first_body: &[u8],
            list_json: Vec<serde_json::Value>,
        ) -> Self {
            let list_body = serde_json::to_vec(&list_json).unwrap();
            self.add_get_response(Some(first_status), Some(first_body), None)
                .add_get_response(Some(200), Some(&list_body), None)
        }

        fn with_list_json(self, json: Vec<serde_json::Value>) -> Self {
            let body = serde_json::to_vec(&json).unwrap();
            self.add_get_response(Some(200), Some(&body), None)
        }

        fn with_get_error(self, message: &str) -> Self {
            self.add_get_response(None, None, Some(message))
        }

        fn with_post_response(self, status: u16, body: &[u8]) -> Self {
            self.add_post_response(Some(status), Some(body), None)
        }

        fn with_post_error(self, message: &str) -> Self {
            self.add_post_response(None, None, Some(message))
        }

        fn with_patch_response(self, status: u16, body: &[u8]) -> Self {
            self.add_patch_response(Some(status), Some(body), None)
        }

        fn with_patch_error(self, message: &str) -> Self {
            self.add_patch_response(None, None, Some(message))
        }
    }

    impl HttpClient for MockClient {
        fn get(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            let idx = self.call_count.get() % self.get_responses.len().max(1);
            let (status, body, err) = &self.get_responses[idx];
            self.call_count.set(idx + 1);

            match err {
                Some(msg) => Err(HttpClientError::Connection(msg.clone())),
                None => match (status, body) {
                    (Some(s), Some(b)) => Ok(HttpResponse {
                        status_code: *s,
                        url: "http://mock".to_string(),
                        headers: HashMap::new(),
                        content: b.clone(),
                    }),
                    _ => Err(HttpClientError::Connection("not configured".to_string())),
                },
            }
        }

        fn post(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            let responses = &self.post_responses;
            if responses.is_empty() {
                return Err(HttpClientError::Connection("not configured".to_string()));
            }
            let (status, body, err) = &responses[0];
            match err {
                Some(msg) => Err(HttpClientError::Connection(msg.clone())),
                None => match (status, body) {
                    (Some(s), Some(b)) => Ok(HttpResponse {
                        status_code: *s,
                        url: "http://mock".to_string(),
                        headers: HashMap::new(),
                        content: b.clone(),
                    }),
                    _ => Err(HttpClientError::Connection("not configured".to_string())),
                },
            }
        }

        fn delete(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }

        fn patch(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            let responses = &self.patch_responses;
            if responses.is_empty() {
                return Err(HttpClientError::Connection("not configured".to_string()));
            }
            let (status, body, err) = &responses[0];
            match err {
                Some(msg) => Err(HttpClientError::Connection(msg.clone())),
                None => match (status, body) {
                    (Some(s), Some(b)) => Ok(HttpResponse {
                        status_code: *s,
                        url: "http://mock".to_string(),
                        headers: HashMap::new(),
                        content: b.clone(),
                    }),
                    _ => Err(HttpClientError::Connection("not configured".to_string())),
                },
            }
        }
    }

    // ─── Route tests ───────────────────────────────────────────────────

    #[test]
    fn route_create_credential_configuration() {
        let args = vec!["credential-configuration", "create", "some-id"];
        assert_eq!(route_command(&args), CommandRoute::CreateCredentialConfiguration);
    }

    #[test]
    fn route_show_credential_configuration() {
        let args = vec!["credential-configuration", "show", "cfg-123"];
        assert_eq!(
            route_command(&args),
            CommandRoute::ShowCredentialConfiguration("cfg-123".to_string())
        );
    }

    #[test]
    fn route_update_credential_configuration() {
        let args = vec!["credential-configuration", "update", "any-id"];
        assert_eq!(route_command(&args), CommandRoute::UpdateCredentialConfiguration);
    }

    #[test]
    fn route_delete_credential_configuration() {
        let args = vec!["credential-configuration", "delete", "cfg-456"];
        assert_eq!(
            route_command(&args),
            CommandRoute::DeleteCredentialConfiguration("cfg-456".to_string())
        );
    }

    #[test]
    fn route_list_credential_configurations() {
        let args = vec!["credential-configuration", "list"];
        assert_eq!(
            route_command(&args),
            CommandRoute::ListCredentialConfigurations
        );
    }

    #[test]
    fn route_revoke_credential() {
        let args = vec!["revoke", "cred-789"];
        assert_eq!(
            route_command(&args),
            CommandRoute::RevokeCredential("cred-789".to_string())
        );
    }

    #[test]
    fn route_empty_args_shows_credential_config_usage() {
        let args: Vec<&str> = vec![];
        assert_eq!(route_command(&args), CommandRoute::ShowCredentialConfigUsage);
    }

    #[test]
    fn route_credential_configuration_only_shows_credential_config_usage() {
        let args = vec!["credential-configuration"];
        assert_eq!(route_command(&args), CommandRoute::ShowCredentialConfigUsage);
    }

    #[test]
    fn route_credential_configuration_with_unknown_subcommand_shows_credential_config_usage() {
        let args = vec!["credential-configuration", "unknown"];
        assert_eq!(route_command(&args), CommandRoute::ShowCredentialConfigUsage);
    }

    #[test]
    fn route_unknown_command_shows_general_usage() {
        let args = vec!["foobar"];
        assert_eq!(route_command(&args), CommandRoute::ShowUsage);
    }

    #[test]
    fn route_revoke_without_id_shows_general_usage() {
        let args = vec!["revoke"];
        assert_eq!(route_command(&args), CommandRoute::ShowUsage);
    }

    // ─── Handler tests ─────────────────────────────────────────────────

    fn make_config_client<C: HttpClient>(mock: C) -> SsiAgentCredentialConfigurationsClient<C> {
        SsiAgentCredentialConfigurationsClient::new(mock, "http://mock")
    }

    fn make_revocation_client<C: HttpClient>(mock: C) -> RevocationClient<C> {
        RevocationClient::new(mock, "http://mock")
    }

    #[test]
    fn handle_list_success() {
        let mock = MockClient::new().with_list_json(vec![
            serde_json::json!({"id": "cfg-1"}),
        ]);
        let client = make_config_client(mock);
        let result = handle_list(&client);
        assert!(result.is_ok());
    }

    #[test]
    fn handle_list_error() {
        let mock = MockClient::new().with_get_error("connection refused");
        let client = make_config_client(mock);
        let result = handle_list(&client);
        assert!(result.is_err());
    }

    #[test]
    fn handle_delete_success() {
        // SsiAgentCredentialConfigurationsClient::delete uses POST internally
        let mock = MockClient::new().with_post_response(200, b"{}");
        let client = make_config_client(mock);
        let result = handle_delete(&client, "cfg-123");
        assert!(result.is_ok());
    }

    #[test]
    fn handle_delete_error() {
        // Client delete doesn't check HTTP status - must return Err from mock
        let mock = MockClient::new().with_post_error("delete failed");
        let client = make_config_client(mock);
        let result = handle_delete(&client, "cfg-missing");
        assert!(result.is_err());
    }

    #[test]
    fn handle_revoke_success() {
        let mock = MockClient::new().with_patch_response(200, b"{}");
        let client = make_revocation_client(mock);
        let result = handle_revoke(&client, "cred-456");
        assert!(result.is_ok());
    }

    #[test]
    fn handle_revoke_error() {
        let mock = MockClient::new().with_patch_error("invalid state");
        let client = make_revocation_client(mock);
        let result = handle_revoke(&client, "cred-bad");
        assert!(result.is_err());
    }

    #[test]
    fn handle_show_direct_get_success() {
        // CredentialConfiguration requires id, type, and name
        let mock = MockClient::new()
            .add_get_response(Some(200), Some(r#"{"id":"cfg-1","type":["VerifiedCertificate"],"name":"test"}"#.as_bytes()), None);
        let client = make_config_client(mock);
        let result = handle_show(&client, "cfg-1");
        assert!(result.is_ok());
    }

    #[test]
    fn handle_show_fallback_list_match() {
        // First GET returns status 0 (fallback triggers list lookup)
        // Second GET (list) returns valid JSON with matching ID
        let mock = MockClient::new()
            .with_fallback_list(0, b"{}", vec![
                serde_json::json!({"id": "cfg-1", "name": "found"}),
                serde_json::json!({"id": "cfg-2", "name": "other"}),
            ]);
        let client = make_config_client(mock);
        let result = handle_show(&client, "cfg-1");
        assert!(result.is_ok());
    }

    #[test]
    fn handle_show_fallback_list_not_found() {
        // First GET returns status 0 (fallback), list returns non-matching config
        let mock = MockClient::new()
            .with_fallback_list(0, b"{}", vec![
                serde_json::json!({"id": "cfg-1", "name": "other"}),
            ]);
        let client = make_config_client(mock);
        let result = handle_show(&client, "cfg-missing");
        assert!(result.is_err());
    }

    #[test]
    fn handle_show_other_http_error() {
        let mock = MockClient::new().with_get_error("service unavailable");
        let client = make_config_client(mock);
        let result = handle_show(&client, "cfg-1");
        assert!(result.is_err());
    }

    #[test]
    fn handle_show_fallback_list_error() {
        // First GET returns status 0 (fallback), list GET returns connection error
        let mock = MockClient::new()
            .add_get_response(Some(0), Some(b"{}"), None)
            .add_get_response(None, None, Some("list failed"));
        let client = make_config_client(mock);
        let result = handle_show(&client, "cfg-1");
        assert!(result.is_err());
    }

    // ─── Execute tests (end-to-end command execution) ──────────────────

    #[test]
    fn execute_list() {
        let mock = MockClient::new().with_list_json(vec![serde_json::json!({"id": "a"})]);
        let config_client = make_config_client(mock);
        let revocation_client = make_revocation_client(MockClient::new());
        let result = execute(
            &["credential-configuration", "list"],
            &config_client,
            &revocation_client,
        );
        assert!(result.is_ok());
    }

    #[test]
    fn execute_delete() {
        // SsiAgentCredentialConfigurationsClient::delete uses POST internally
        let mock = MockClient::new().with_post_response(200, b"{}");
        let config_client = make_config_client(mock);
        let revocation_client = make_revocation_client(MockClient::new());
        let result = execute(
            &["credential-configuration", "delete", "cfg-1"],
            &config_client,
            &revocation_client,
        );
        assert!(result.is_ok());
    }

    #[test]
    fn execute_delete_error() {
        let mock = MockClient::new().with_post_error("delete failed");
        let config_client = make_config_client(mock);
        let revocation_client = make_revocation_client(MockClient::new());
        let result = execute(
            &["credential-configuration", "delete", "cfg-1"],
            &config_client,
            &revocation_client,
        );
        assert!(result.is_err());
    }

    #[test]
    fn execute_revoke() {
        let mock = MockClient::new().with_patch_response(200, b"{}");
        let config_client = make_config_client(MockClient::new());
        let revocation_client = make_revocation_client(mock);
        let result = execute(
            &["revoke", "cred-1"],
            &config_client,
            &revocation_client,
        );
        assert!(result.is_ok());
    }

    #[test]
    fn execute_show_usage_for_empty_args() {
        let config_client = make_config_client(MockClient::new());
        let revocation_client = make_revocation_client(MockClient::new());
        let result = execute(&[], &config_client, &revocation_client);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Missing arguments");
    }

    #[test]
    fn execute_show_general_usage_for_unknown() {
        let config_client = make_config_client(MockClient::new());
        let revocation_client = make_revocation_client(MockClient::new());
        let result = execute(
            &["unknown-command"],
            &config_client,
            &revocation_client,
        );
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Unknown command");
    }
}
