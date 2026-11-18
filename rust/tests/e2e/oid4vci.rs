/// E2E tests for the OID4VCI flow and credential metadata.
use super::support::admin_client::AdminHttpClient;
use super::support::browser::Browser;
use super::support::config::Config;
use super::support::http_client::HttpClient;
use super::support::verifier::Verifier;
use super::support::wallet::WalletClient;

const CREDENTIAL_TYPES: [&str; 2] = ["ob3", "edc"];

fn admin_client() -> AdminHttpClient {
    AdminHttpClient::new(HttpClient::new(&Config::new()))
}

fn wallet_client() -> WalletClient {
    WalletClient::new(HttpClient::new(&Config::new()))
}

/// Run the full wallet flow for a created offer and return the credential.
async fn issue_credential(credential_type: &str) -> super::support::wallet::VerifiableCredential {
    let create_offer_response = admin_client()
        .create_offer("award-123", credential_type)
        .await;

    let mut wallet = wallet_client();
    let (offer, metadata, auth_url) = wallet.use_offer(&create_offer_response.uri).await;

    let callback_url = Browser::new().open(&auth_url).await;
    wallet
        .open_callback_url(&callback_url, &offer, &metadata)
        .await
}

macro_rules! oid4vci_type_tests {
    ($iss_test:ident, $type_test:ident) => {
        #[tokio::test]
        async fn $iss_test() {
            for credential_type in CREDENTIAL_TYPES {
                let credential = issue_credential(credential_type).await;
                assert_eq!(credential.claims["iss"], "did:web:localhost%3A8001");
            }
        }

        #[tokio::test]
        async fn $type_test() {
            for credential_type in CREDENTIAL_TYPES {
                let credential = issue_credential(credential_type).await;
                let types = credential.claims["type"]
                    .as_array()
                    .expect("Credential type must be a list");
                assert!(
                    types.iter().any(|t| t == "VerifiableCredential"),
                    "Credential type list must contain VerifiableCredential"
                );
            }
        }
    };
}

oid4vci_type_tests!(
    test_get_credential_credential_type,
    test_get_credential_type
);

#[tokio::test]
async fn test_get_verify_credential() {
    let credential = issue_credential("ob3").await;
    let verifier = Verifier::new(HttpClient::new(&Config::new()));
    assert!(
        verifier
            .verify(&credential.jwt, &credential.issuer_did())
            .await
    );
}
