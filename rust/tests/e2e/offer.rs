/// E2E tests for the offer endpoints.
use super::support::admin_client::AdminHttpClient;
use super::support::config::Config;
use super::support::http_client::HttpClient;
use super::support::utilities::assert_schema;
use super::support::wallet::Offer;

const CREDENTIAL_TYPES: [&str; 2] = ["ob3", "edc"];

fn admin_client() -> AdminHttpClient {
    AdminHttpClient::new(HttpClient::new(&Config::new()))
}

fn http_client() -> HttpClient {
    HttpClient::new(&Config::new())
}

/// Extract the `credential_offer_uri` query parameter from an offer URI.
fn credential_offer_uri(offer_uri: &str) -> String {
    let parsed = url::Url::parse(offer_uri).expect("offer uri is not a valid URL");
    parsed
        .query_pairs()
        .find(|(k, _)| k == "credential_offer_uri")
        .map(|(_, v)| v.into_owned())
        .expect("credential_offer_uri not found in offer uri")
}

macro_rules! offer_tests {
    ($create:ident, $get:ident, $auth_code:ident) => {
        #[tokio::test]
        async fn $create() {
            for credential_type in CREDENTIAL_TYPES {
                let config = Config::new();
                let response = admin_client()
                    .create_offer("award-123", credential_type)
                    .await;

                let value = serde_json::to_value(&response).unwrap();
                assert_schema(&value, "create_offer_response");

                // Fixed in mock-ssi-agent: should be the uuid in offer_id
                let offer_id = "offer-123";
                let parsed = credential_offer_uri(&response.uri);
                assert_eq!(
                    parsed,
                    format!("{}/openid4vci/offers/{offer_id}", config.ssi_agent_url)
                );
            }
        }

        #[tokio::test]
        async fn $get() {
            for credential_type in CREDENTIAL_TYPES {
                let config = Config::new();
                let create_response = admin_client()
                    .create_offer("award-123", credential_type)
                    .await;
                let uri = credential_offer_uri(&create_response.uri);
                let response = http_client().get(&uri, None).await;

                assert_eq!(response.status().as_u16(), 200);
                let body: serde_json::Value = response.json().await.unwrap();
                let offer: Offer = serde_json::from_value(body.clone()).unwrap();

                assert_schema(&body, "credential_offer");
                assert_eq!(offer.credential_issuer, config.ssi_agent_url);
            }
        }

        #[tokio::test]
        async fn $auth_code() {
            for credential_type in CREDENTIAL_TYPES {
                let create_response = admin_client()
                    .create_offer("award-123", credential_type)
                    .await;
                let uri = credential_offer_uri(&create_response.uri);
                let response = http_client().get(&uri, None).await;
                let offer: Offer = response.json().await.unwrap();

                assert!(!offer.issuer_state().is_empty());
            }
        }
    };
}

offer_tests!(
    test_create_offer,
    test_get_offer,
    test_offer_is_authorization_code_flow
);
