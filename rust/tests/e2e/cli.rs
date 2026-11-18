/// E2E tests for the credential-configuration CLI commands.
///
/// Runs the compiled `cli` binary (via `CARGO_BIN_EXE_cli`) against the mock SSI agent.
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

const TESTS_E2E_DIR: &str = env!("CARGO_MANIFEST_DIR");

struct CliOutput {
    status: std::process::ExitStatus,
    stdout: String,
    stderr: String,
}

fn run_cli(args: &[&str], stdin_input: Option<&str>) -> CliOutput {
    let mut child = Command::new(env!("CARGO_BIN_EXE_cli"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("Failed to spawn cli binary");

    if let Some(input) = stdin_input {
        child
            .stdin
            .as_mut()
            .expect("stdin not piped")
            .write_all(input.as_bytes())
            .expect("Failed to write to stdin");
    }

    let output = child.wait_with_output().expect("Failed to wait on cli");
    CliOutput {
        status: output.status,
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
    }
}

fn credential_configuration_input() -> String {
    let path = PathBuf::from(format!(
        "{TESTS_E2E_DIR}/tests/e2e/fixtures/openbadge_credential_template.json"
    ));
    std::fs::read_to_string(path).expect("Failed to read fixture")
}

fn assert_credential_config_output(output: &serde_json::Value) {
    assert_eq!(output["id"], "OpenbadgeCredential");
    assert_eq!(output["display"]["name"], "Open Badge Credential");
    assert_eq!(
        output["type"],
        serde_json::json!(["VerifiableCredential", "OpenBadgeCredential"])
    );
}

#[test]
fn test_create_credential_configuration() {
    let result = run_cli(
        &["credential-configuration", "create", "OpenbadgeCredential"],
        Some(&credential_configuration_input()),
    );
    assert!(result.status.success(), "Create failed: {}", result.stderr);
    let output: serde_json::Value = serde_json::from_str(&result.stdout).expect("Invalid JSON");
    assert_credential_config_output(&output);
}

#[test]
fn test_list_credential_configurations() {
    let result = run_cli(&["credential-configuration", "list"], None);
    assert!(result.status.success(), "List failed: {}", result.stderr);
    let output: Vec<serde_json::Value> =
        serde_json::from_str(&result.stdout).expect("Invalid JSON");
    assert!(output.iter().any(|c| c["id"] == "OpenbadgeCredential"));
}

#[test]
fn test_show_credential_configuration() {
    let result = run_cli(
        &["credential-configuration", "show", "OpenbadgeCredential"],
        None,
    );
    assert!(result.status.success(), "Show failed: {}", result.stderr);
    let output: serde_json::Value = serde_json::from_str(&result.stdout).expect("Invalid JSON");
    assert_credential_config_output(&output);
}

#[test]
fn test_update_credential_configuration() {
    let create = run_cli(
        &["credential-configuration", "create", "OpenbadgeCredential"],
        Some(&credential_configuration_input()),
    );
    assert!(create.status.success(), "Create failed: {}", create.stderr);

    let result = run_cli(
        &["credential-configuration", "update", "OpenbadgeCredential"],
        Some(&credential_configuration_input()),
    );
    assert!(result.status.success(), "Update failed: {}", result.stderr);
    let output: serde_json::Value = serde_json::from_str(&result.stdout).expect("Invalid JSON");
    assert_eq!(output["id"], "OpenbadgeCredential");
}

#[test]
fn test_invalid_command() {
    let result = run_cli(&["credential-configuration", "invalid"], None);
    assert_eq!(result.status.code(), Some(1));
    assert!(result.stderr.contains("Usage:"));
}

#[test]
fn test_show_nonexistent() {
    let result = run_cli(&["credential-configuration", "show", "nonexistent"], None);
    assert_eq!(result.status.code(), Some(1));
    assert!(result.stderr.contains("Error:"));
}

#[test]
fn test_delete_credential_configuration() {
    let create = run_cli(
        &["credential-configuration", "create", "OpenbadgeCredential"],
        Some(&credential_configuration_input()),
    );
    assert!(create.status.success(), "Create failed: {}", create.stderr);

    let show = run_cli(
        &["credential-configuration", "show", "OpenbadgeCredential"],
        None,
    );
    assert!(show.status.success(), "Show failed: {}", show.stderr);

    let result = run_cli(
        &["credential-configuration", "delete", "OpenbadgeCredential"],
        None,
    );
    assert!(result.status.success(), "Delete failed: {}", result.stderr);
    assert!(result.stdout.to_lowercase().contains("deleted"));
}

#[test]
fn test_delete_nonexistent_returns_success() {
    let result = run_cli(
        &[
            "credential-configuration",
            "delete",
            "nonexistent-template-id",
        ],
        None,
    );
    assert!(result.status.success(), "Delete failed: {}", result.stderr);
    assert!(result.stdout.to_lowercase().contains("deleted"));
}
