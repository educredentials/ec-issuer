use assert_cmd::cargo;
use reqwest::StatusCode;
use std::process::{Child, Command};
use std::thread;
use std::time::Duration;

#[tokio::test]
async fn test_hello_world_endpoint() {
    let server_process = start_server_process(3001).expect("Failed to start server");
    let test_control = TestControl::new(server_process);
    thread::sleep(Duration::from_secs(2));

    let client = reqwest::Client::new();
    let response = client
        .get("http://localhost:3001/") // Use different port for tests
        .send()
        .await
        .expect("Failed to make HTTP request");

    // Assertions
    assert_eq!(response.status(), StatusCode::OK);
    let body = response.text().await.expect("Failed to read response body");
    assert_eq!(body, "Hello, world!");

    drop(test_control);
}

struct TestControl {
    service: Child,
}

impl TestControl {
    fn new(service: Child) -> Self {
        Self { service }
    }
}

impl Drop for TestControl {
    fn drop(&mut self) {
        self.service.kill().expect("Stop service process");
    }
}

fn start_server_process(port: u16) -> Result<Child, std::io::Error> {
    std::env::set_var("SERVER_HOST", "localhost");
    std::env::set_var("SERVER_PORT", port.to_string()); // Different port for tests
    std::env::set_var("DATABASE_URL", "sqlite::memory:");
    std::env::set_var("SIGNING_USE_GRPC", "false");
    std::env::set_var("SIGNING_SERVICE_URL", "http://localhost:50051");

    let mut command = Command::new(cargo::cargo_bin!("ec-issuer"));

    command.spawn()
}
