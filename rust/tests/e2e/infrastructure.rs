/// E2E tests for infrastructure endpoints (health, root, CORS, metrics).
use super::support::config::Config;
use super::support::http_client::HttpClient;

fn http_client() -> HttpClient {
    HttpClient::new(&Config::new())
}

#[tokio::test]
async fn test_health_success() {
    let response = http_client().get("/health", None).await;
    assert_eq!(response.status().as_u16(), 200);
    let body: serde_json::Value = response.json().await.unwrap();
    assert_eq!(
        body,
        serde_json::json!({"status": "healthy", "database": "ok"})
    );
}

#[tokio::test]
async fn test_root_endpoint() {
    let response = http_client().get("/", None).await;
    assert_eq!(response.status().as_u16(), 200);
    assert_eq!(response.text().await.unwrap(), "Hello, World!");
}

#[tokio::test]
async fn test_root_endpoint_returns_cors_headers() {
    let response = http_client()
        .get("/", Some(&[("Origin", "http://localhost:3000")]))
        .await;
    assert_eq!(response.status().as_u16(), 200);
    let allow_origin = response
        .headers()
        .get("Access-Control-Allow-Origin")
        .expect("Missing Access-Control-Allow-Origin header")
        .to_str()
        .unwrap();
    assert_eq!(allow_origin, "http://localhost:3000");
}

#[tokio::test]
async fn test_metrics_endpoint_returns_prometheus_metrics() {
    let client = http_client();
    let response = client.get("/", None).await;
    assert_eq!(response.status().as_u16(), 200);

    let response = client.get("/metrics", None).await;
    assert_eq!(response.status().as_u16(), 200);
    let text = response.text().await.unwrap();
    assert!(
        text.contains("axum_http_requests_total{method=\"GET\",status=\"200\",endpoint=\"/\"}"),
        "metrics output missing axum_http_requests_total for GET /:\n{text}"
    );
    assert!(
        text.contains("# HELP") || text.contains("# TYPE"),
        "metrics output missing HELP/TYPE lines:\n{text}"
    );
}
