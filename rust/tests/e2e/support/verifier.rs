/// Verifier client for e2e tests.
use serde::Deserialize;

use super::http_client::HttpClient;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct VerificationMethod {
    pub id: String,
    pub r#type: String,
    pub controller: String,
    pub public_key_jwk: serde_json::Value,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DidDocument {
    pub id: String,
    pub verification_method: Vec<VerificationMethod>,
    pub authentication: Vec<String>,
    pub assertion_method: Vec<String>,
}

pub struct Verifier {
    http_client: HttpClient,
}

impl Verifier {
    pub fn new(http_client: HttpClient) -> Self {
        Self { http_client }
    }

    /// Verify a credential JWT by resolving the issuer did:web and checking the EdDSA signature.
    pub async fn verify(&self, credential_jwt: &str, issuer_did: &str) -> bool {
        let did_document = self.resolve_did_web(issuer_did).await;
        assert!(
            !did_document.verification_method.is_empty(),
            "No verification methods found in DID document"
        );
        let public_key_jwk = &did_document.verification_method[0].public_key_jwk;

        let jwk: jsonwebtoken::jwk::Jwk =
            serde_json::from_value(public_key_jwk.clone()).expect("Invalid JWK in DID document");
        let decoding_key = jsonwebtoken::DecodingKey::from_jwk(&jwk)
            .expect("Failed to build decoding key from JWK");
        let mut validation = jsonwebtoken::Validation::new(jsonwebtoken::Algorithm::EdDSA);
        // The mock credential JWT has no exp claim; like PyJWT, validate
        // expiration only when the claim is present.
        validation.required_spec_claims.clear();
        validation.set_issuer(&[issuer_did]);

        jsonwebtoken::decode::<serde_json::Value>(credential_jwt, &decoding_key, &validation)
            .is_ok()
    }

    async fn resolve_did_web(&self, did_web: &str) -> DidDocument {
        assert!(did_web.starts_with("did:web:"), "Expected did:web: DID");
        let method_specific_id = &did_web[8..]; // Remove "did:web:"

        let mut path = method_specific_id.replace(':', "/");
        path = path.replace("%3A", ":");

        // Non-standard: allow http for localhost
        let url = if path.starts_with("localhost") {
            format!("http://{path}")
        } else {
            format!("https://{path}")
        };

        let url = format!("{url}/.well-known/did.json");

        let response = self.http_client.get(&url, None).await;
        assert!(
            response.status().as_u16() == 200,
            "Expected 200, got {}: {}",
            response.status(),
            response
                .text()
                .await
                .unwrap_or_default()
                .chars()
                .take(200)
                .collect::<String>()
        );

        let did_document: DidDocument = response.json().await.unwrap();
        assert_eq!(did_document.id, did_web, "DID mismatch");
        did_document
    }
}
