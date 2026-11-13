/// CLI binary for the Educredentials Issuer.
///
/// Provides sysadmin commands for managing credential configurations and revoking credentials.
use std::io::Read;

use ec_issuer::config::Config;
use ec_issuer::credential_configurations::ssi_agent::SsiAgentCredentialConfigurationsClient;
use ec_issuer::helpers::reqwest_client::ReqwestHttpClient;
use ec_issuer::revocation::client::RevocationClient;

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

    match args_ref.as_slice() {
        ["credential-configuration", "create", _config_id] => {
            handle_create(&config_client);
        }
        ["credential-configuration", "show", config_id] => {
            handle_show(&config_client, config_id);
        }
        ["credential-configuration", "update", _config_id] => {
            handle_create(&config_client);
        }
        ["credential-configuration", "delete", config_id] => {
            handle_delete(&config_client, config_id);
        }
        ["credential-configuration", "list"] => {
            handle_list(&config_client);
        }
        [] | ["credential-configuration"] | ["credential-configuration", ..] => {
            eprintln!("{CREDENTIAL_CONFIG_USAGE}");
            std::process::exit(1);
        }
        ["revoke", credential_id] => {
            handle_revoke(&revocation_client, credential_id);
        }
        _ => {
            eprintln!("{USAGE}");
            std::process::exit(1);
        }
    }
}

fn handle_create(client: &SsiAgentCredentialConfigurationsClient<ReqwestHttpClient>) {
    let mut input = String::new();
    if let Err(e) = std::io::stdin().read_to_string(&mut input) {
        eprintln!("Error: Failed to read stdin: {e}");
        std::process::exit(1);
    }

    let config: serde_json::Value = match serde_json::from_str(&input) {
        Ok(v) => v,
        Err(e) => {
            eprintln!("Error: Invalid JSON: {e}");
            std::process::exit(1);
        }
    };

    match client.create(&config) {
        Ok(result) => println!("{}", serde_json::to_string(&result).unwrap()),
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}

fn handle_show(
    client: &SsiAgentCredentialConfigurationsClient<ReqwestHttpClient>,
    config_id: &str,
) {
    match client.get(config_id) {
        Ok(config) => println!("{}", serde_json::to_string(&config).unwrap()),
        Err(ec_issuer::helpers::http_client::HttpClientError::Http { status: 0, .. }) =>
        {
            // Try list-based lookup
            match client.list() {
                Ok(templates) => {
                    for template in templates {
                        if let Some(id) = template.get("id").and_then(|v| v.as_str()) {
                            if id == config_id {
                                println!("{}", serde_json::to_string(&template).unwrap());
                                return;
                            }
                        }
                    }
                    eprintln!("Error: Configuration not found: {config_id}");
                    std::process::exit(1);
                }
                Err(e) => {
                    eprintln!("Error: {e}");
                    std::process::exit(1);
                }
            }
        }
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}

fn handle_list(client: &SsiAgentCredentialConfigurationsClient<ReqwestHttpClient>) {
    match client.list() {
        Ok(templates) => println!("{}", serde_json::to_string(&templates).unwrap()),
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}

fn handle_delete(
    client: &SsiAgentCredentialConfigurationsClient<ReqwestHttpClient>,
    config_id: &str,
) {
    match client.delete(config_id) {
        Ok(()) => println!("Configuration \"{config_id}\" deleted"),
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}

fn handle_revoke(client: &RevocationClient<ReqwestHttpClient>, credential_id: &str) {
    match client.revoke_via_ssi_agent(credential_id) {
        Ok(()) => println!("Credential \"{credential_id}\" revoked"),
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    }
}
