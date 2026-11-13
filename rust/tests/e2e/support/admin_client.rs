/// Admin HTTP client for e2e tests.

use serde::{Deserialize, Serialize};

use super::http_client::HttpClient;

#[derive(Debug, Deserialize, Serialize)]
pub struct CreateOfferResponse {
    pub offer_id: String,
    pub uri: String,
}

pub struct AdminHttpClient {
    client: HttpClient,
}

impl AdminHttpClient {
    pub fn new(client: HttpClient) -> Self {
        Self { client }
    }

    pub async fn create_offer(
        &self,
        award_id: &str,
        credential_type: &str,
    ) -> CreateOfferResponse {
        let json = serde_json::json!({
            "award_id": award_id,
            "credential_type": credential_type,
        });

        let response = self
            .client
            .post(
                "api/v1/offers",
                Some(&json),
                Some(&[
                    ("Authorization", "Bearer test-token"),
                    ("Content-Type", "application/json"),
                ]),
            )
            .await;

        assert!(
            response.status().as_u16() == 201,
            "Expected 201 Created, got {}: {}",
            response.status(),
            response.text().await.unwrap_or_default().chars().take(200)
        );

        response
            .json::<CreateOfferResponse>()
            .await
            .expect("Failed to parse CreateOfferResponse")
    }
}
