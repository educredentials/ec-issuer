/// Reqwest-based HTTP client implementation.
use std::collections::HashMap;
use std::sync::Arc;

use super::http_client::{HttpClient, HttpClientError, HttpResponse};

/// HTTP client implementation using reqwest blocking API.
pub struct ReqwestHttpClient {
    client: reqwest::blocking::Client,
}

impl ReqwestHttpClient {
    /// Create a new reqwest HTTP client.
    #[must_use]
    pub fn new() -> Self {
        Self {
            client: reqwest::blocking::Client::new(),
        }
    }
}

impl Default for ReqwestHttpClient {
    fn default() -> Self {
        Self::new()
    }
}

impl HttpClient for ReqwestHttpClient {
    fn get(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
    ) -> Result<HttpResponse, HttpClientError> {
        let mut request = self.client.get(url);
        for (k, v) in headers {
            request = request.header(k, v);
        }
        self._process_response(request.send())
    }

    fn post(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
        body: &str,
    ) -> Result<HttpResponse, HttpClientError> {
        let body = body.to_string();
        let mut request = self.client.post(url).body(body);
        for (k, v) in headers {
            request = request.header(k, v);
        }
        self._process_response(request.send())
    }

    fn delete(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
    ) -> Result<HttpResponse, HttpClientError> {
        let mut request = self.client.delete(url);
        for (k, v) in headers {
            request = request.header(k, v);
        }
        self._process_response(request.send())
    }

    fn patch(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
        body: &str,
    ) -> Result<HttpResponse, HttpClientError> {
        let body = body.to_string();
        let mut request = self.client.patch(url).body(body);
        for (k, v) in headers {
            request = request.header(k, v);
        }
        self._process_response(request.send())
    }
}

impl ReqwestHttpClient {
    fn _process_response(
        &self,
        response: Result<reqwest::blocking::Response, reqwest::Error>,
    ) -> Result<HttpResponse, HttpClientError> {
        match response {
            Ok(resp) => {
                let status = resp.status().as_u16();
                let url = resp.url().to_string();
                let headers: HashMap<String, String> = resp
                    .headers()
                    .iter()
                    .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("").to_string()))
                    .collect();
                let content = resp.bytes().unwrap_or_default().to_vec();
                Ok(HttpResponse {
                    status_code: status,
                    url,
                    headers,
                    content,
                })
            }
            Err(e) => Err(HttpClientError::Connection(e.to_string())),
        }
    }
}

/// Arc-wrapped reqwest HTTP client for use with `'static` trait objects.
#[derive(Clone)]
pub struct ReqwestHttpClientArc {
    inner: Arc<ReqwestHttpClient>,
}

impl ReqwestHttpClientArc {
    /// Create a new wrapped reqwest HTTP client.
    #[must_use]
    pub fn new() -> Self {
        Self {
            inner: Arc::new(ReqwestHttpClient::new()),
        }
    }
}

impl Default for ReqwestHttpClientArc {
    fn default() -> Self {
        Self::new()
    }
}

impl HttpClient for ReqwestHttpClientArc {
    fn get(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
    ) -> Result<HttpResponse, HttpClientError> {
        self.inner.get(url, headers)
    }

    fn post(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
        body: &str,
    ) -> Result<HttpResponse, HttpClientError> {
        self.inner.post(url, headers, body)
    }

    fn delete(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
    ) -> Result<HttpResponse, HttpClientError> {
        self.inner.delete(url, headers)
    }

    fn patch(
        &self,
        url: &str,
        headers: &HashMap<String, String>,
        body: &str,
    ) -> Result<HttpResponse, HttpClientError> {
        self.inner.patch(url, headers, body)
    }
}
