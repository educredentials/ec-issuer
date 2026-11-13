/// Fake browser for simulating OIDC flows.

use reqwest::Client;

pub struct Browser {
    client: Client,
}

impl Browser {
    pub fn new() -> Self {
        Self {
            client: Client::builder()
                .redirect(reqwest::redirect::Policy::none())
                .build()
                .expect("Failed to build browser client"),
        }
    }

    /// Follow redirects until we hit a `mywallet://` deeplink.
    pub async fn open(&self, url: &str) -> String {
        let mut current_url = url.to_string();
        loop {
            let resp = self
                .client
                .get(&current_url)
                .header("Accept", "text/html")
                .send()
                .await
                .expect("GET request failed");

            let status = resp.status().as_u16();
            assert!(
                matches!(status, 301 | 302 | 303 | 307 | 308),
                "Expected redirect, got {}: {}",
                status,
                resp.text().await.unwrap_or_default().chars().take(200)
            );

            let location = resp
                .headers()
                .get("Location")
                .expect("Missing Location header")
                .to_str()
                .expect("Location header not UTF-8")
                .to_string();

            if location.starts_with("mywallet://") {
                return location;
            }
            current_url = location;
        }
    }
}
