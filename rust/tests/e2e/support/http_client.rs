/// HTTP client for e2e tests.

use reqwest::Client;
use serde::{Deserialize, Serialize};

use super::config::Config;

#[derive(Clone)]
pub struct HttpClient {
    client: Client,
    base_url: String,
}

impl HttpClient {
    pub fn new(config: &Config) -> Self {
        Self {
            client: Client::new(),
            base_url: config.ec_issuer_url.clone(),
        }
    }

    pub async fn get(&self, path: &str, headers: Option<&[(&str, &str)]>) -> reqwest::Response {
        let url = self._build_url(path);
        let mut request = self.client.get(&url);
        if let Some(h) = headers {
            for (k, v) in h {
                request = request.header(k, *v);
            }
        }
        request.send().await.expect("GET request failed")
    }

    pub async fn post(
        &self,
        path: &str,
        json: Option<&serde_json::Value>,
        headers: Option<&[(&str, &str)]>,
    ) -> reqwest::Response {
        let url = self._build_url(path);
        let mut request = self.client.post(&url);
        if let Some(body) = json {
            request = request.json(body);
        }
        if let Some(h) = headers {
            for (k, v) in h {
                request = request.header(k, *v);
            }
        }
        request.send().await.expect("POST request failed")
    }

    fn _build_url(&self, path: &str) -> String {
        if path.starts_with("http://") || path.starts_with("https://") {
            path.to_string()
        } else {
            format!("{}/{}", self.base_url, path)
        }
    }
}
