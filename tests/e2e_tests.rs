use assert_cmd::cargo;
use portpicker::pick_unused_port;
use reqwest::StatusCode;
use std::process::{Child, Command};
use std::thread;
use std::time::Duration;

#[tokio::test]
async fn test_hello_world_endpoint() {
    let test_control = start_server_process();

    let client = reqwest::Client::new();
    let response = client
        .get(&format!("http://localhost:{}/", &test_control.port))
        .send()
        .await
        .expect("Failed to make HTTP request");

    // Assertions
    assert_eq!(response.status(), StatusCode::OK);
    let body = response.text().await.expect("Failed to read response body");
    assert_eq!(body, "Hello, world!");

    drop(test_control);
}

#[tokio::test]
async fn test_health_success() {
    let test_control = start_server_process();

    let client = reqwest::Client::new();
    let response = client
        .get(&format!("http://localhost:{}/health", &test_control.port))
        .send()
        .await
        .expect("Failed to make HTTP request");

    // Assertions
    assert_eq!(response.status(), StatusCode::OK);
    let body = response.text().await.expect("Failed to read response body");
    assert_eq!(body, "OK");

    drop(test_control);
}

struct TestControl {
    service: Child,
    port: u16,
}

impl TestControl {
    fn new(service: Child, port: u16) -> Self {
        Self { service, port }
    }
}

impl Drop for TestControl {
    fn drop(&mut self) {
        // Attempt to kill the process gracefully
        let _ = self.service.kill();
        // Wait for the process to exit
        let _ = self.service.wait();
    }
}

fn start_server_process() -> TestControl {
    let port = pick_unused_port().expect("Failed to find an unused port");

    let child = Command::new(cargo::cargo_bin!("ec-issuer"))
        .env_clear()
        .envs(vec![
            ("RUST_LOG", "error"),
            ("SERVER_HOST", "localhost"),
            ("SERVER_PORT", &port.to_string()),
            ("DATABASE_URL", "sqlite::memory:"),
            ("SIGNING_USE_GRPC", "false"),
            ("SIGNING_SERVICE_URL", "http://localhost:50051"),
        ])
        .spawn()
        .expect("Failed to start server");

    // Wait for the server to start listening on the port
    // TODO: Implement a detection mechanism to ensure the server is up and running
    thread::sleep(Duration::from_secs(1));

    TestControl::new(child, port)
}
