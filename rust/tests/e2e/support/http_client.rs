/// HTTP client for e2e tests.
use reqwest::Client;

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
            // Trim a trailing slash so relative paths join without double slashes.
            base_url: config.ec_issuer_url.trim_end_matches('/').to_string(),
        }
    }

    pub async fn get(&self, path: &str, headers: Option<&[(&str, &str)]>) -> reqwest::Response {
        let url = self._build_url(path);
        let mut request = self.client.get(&url);
        if let Some(h) = headers {
            for (k, v) in h {
                request = request.header(*k, *v);
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
                request = request.header(*k, *v);
            }
        }
        request.send().await.expect("POST request failed")
    }

    /// POST a pre-encoded form body, as required by OAuth endpoints.
    ///
    /// # Arguments
    ///
    /// * `path` - Absolute URL or path relative to the base URL.
    /// * `form` - URL-encoded form body, e.g. from `serde_urlencoded`.
    /// * `headers` - Optional extra headers.
    pub async fn post_form(
        &self,
        path: &str,
        form: &str,
        headers: Option<&[(&str, &str)]>,
    ) -> reqwest::Response {
        let url = self._build_url(path);
        let mut request = self
            .client
            .post(&url)
            .header(
                reqwest::header::CONTENT_TYPE,
                "application/x-www-form-urlencoded",
            )
            .body(form.to_string());
        if let Some(h) = headers {
            for (k, v) in h {
                request = request.header(*k, *v);
            }
        }
        request.send().await.expect("POST request failed")
    }

    fn _build_url(&self, path: &str) -> String {
        if path.starts_with("http://") || path.starts_with("https://") {
            path.to_string()
        } else if path.starts_with('/') {
            format!("{}{}", self.base_url, path)
        } else {
            format!("{}/{}", self.base_url, path)
        }
    }
}
