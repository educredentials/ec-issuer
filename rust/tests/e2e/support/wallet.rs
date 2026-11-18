/// Wallet client for e2e tests.
///
/// Implements the OID4VCI wallet flow: parse offer → PAR → redirect → callback → token → credential.
use std::path::PathBuf;

use data_encoding::BASE64URL_NOPAD;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use super::browser::Browser;
use super::credential_issuer_metadata::CredentialIssuerMetadata;
use super::http_client::HttpClient;

const _TESTS_E2E_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct AccessTokenResponse {
    access_token: String,
    token_type: String,
    #[serde(default)]
    expires_in: Option<i64>,
    #[serde(default)]
    refresh_token: Option<String>,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct OpenidConfiguration {
    authorization_endpoint: String,
    issuer: String,
    pushed_authorization_request_endpoint: String,
    require_pushed_authorization_requests: bool,
    token_endpoint: String,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct Offer {
    pub credential_issuer: String,
    pub credential_configuration_ids: Vec<String>,
    pub grants: serde_json::Value,
}

impl Offer {
    pub fn issuer_state(&self) -> String {
        let grants = self
            .grants
            .get("authorization_code")
            .expect("Offer is not authorization code flow");
        grants
            .get("issuer_state")
            .and_then(|v| v.as_str())
            .expect("Missing issuer_state in authorization_code grant")
            .to_string()
    }
}

#[derive(Debug, Deserialize)]
pub struct CredentialResponse {
    credentials: Vec<CredentialEntry>,
}

#[derive(Debug, Deserialize)]
struct CredentialEntry {
    credential: String,
}

#[derive(Debug, Clone)]
pub struct VerifiableCredential {
    pub jwt: String,
    pub claims: serde_json::Value,
}

impl VerifiableCredential {
    pub fn from_jwt(jwt_str: &str) -> Self {
        let parts: Vec<&str> = jwt_str.split('.').collect();
        let claims_b64 = parts.get(1).expect("JWT must have 3 parts");
        let padded = format!(
            "{}{}",
            claims_b64,
            "=".repeat((4 - claims_b64.len() % 4) % 4)
        );
        let decoded = BASE64URL_NOPAD.decode(padded.as_bytes()).unwrap();
        let claims: serde_json::Value = serde_json::from_slice(&decoded).unwrap();
        Self {
            jwt: jwt_str.to_string(),
            claims,
        }
    }

    pub fn issuer_did(&self) -> String {
        self.claims
            .get("iss")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string()
    }
}

/// Generate a PKCE code challenge from a code verifier.
fn generate_code_challenge(code_verifier: &str) -> String {
    let hash = Sha256::digest(code_verifier.as_bytes());
    BASE64URL_NOPAD.encode(&hash)
}

/// Generate a random PKCE code verifier.
fn generate_code_verifier() -> String {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let bytes: Vec<u8> = (0..64).map(|_| rng.gen_range(b'a'..=b'z')).collect();
    String::from_utf8(bytes).unwrap()
}

pub struct WalletClient {
    http_client: HttpClient,
    browser: Browser,
    client_id: String,
    deeplink: String,
    code_verifier: Option<String>,
    keys_dir: PathBuf,
}

impl WalletClient {
    pub fn new(http_client: HttpClient) -> Self {
        Self {
            http_client,
            browser: Browser::new(),
            client_id: "MyWallet".to_string(),
            deeplink: "mywallet://return/".to_string(),
            code_verifier: None,
            keys_dir: PathBuf::from(format!("{_TESTS_E2E_DIR}/tests/e2e/keys")),
        }
    }

    pub async fn use_offer(
        &mut self,
        offer_uri: &str,
    ) -> (Offer, CredentialIssuerMetadata, String) {
        let offer = self.get_offer(offer_uri).await;
        let metadata = self.get_issuer_metadata(&offer).await;

        let auth_metadata = self
            .get_auth_metadata(metadata.authorization_server())
            .await;

        let code_verifier = generate_code_verifier();
        let code_challenge = generate_code_challenge(&code_verifier);
        self.code_verifier = Some(code_verifier.clone());

        let config_id = offer
            .credential_configuration_ids
            .first()
            .cloned()
            .unwrap_or_default();
        let auth_details = serde_json::json!([
            {
                "type": "openid_credential",
                "credential_configuration_id": config_id
            }
        ]);

        let auth_attributes = serde_urlencoded::to_string(serde_json::json!({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.deeplink,
            "scope": "openid profile email",
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "authorization_details": auth_details.to_string(),
            "state": "static_state",
            "issuer_state": offer.issuer_state(),
        }))
        .unwrap();

        let par_response = self
            .http_client
            .post_form(
                &auth_metadata.pushed_authorization_request_endpoint,
                &auth_attributes,
                None,
            )
            .await;

        assert!(
            par_response.status().as_u16() == 201,
            "Expected 201, got {}: {}",
            par_response.status(),
            par_response
                .text()
                .await
                .unwrap_or_default()
                .chars()
                .take(200)
                .collect::<String>()
        );

        let par_resp: serde_json::Value = par_response.json().await.unwrap();
        let request_uri = par_resp["request_uri"]
            .as_str()
            .expect("request_uri not found");

        let auth_url = format!(
            "{}?client_id={}&request_uri={}",
            auth_metadata.authorization_endpoint,
            urlencoding::encode(&self.client_id),
            urlencoding::encode(request_uri)
        );

        (offer, metadata, auth_url)
    }

    pub async fn open_callback_url(
        &self,
        callback_url: &str,
        offer: &Offer,
        metadata: &CredentialIssuerMetadata,
    ) -> VerifiableCredential {
        let query = parse_query(callback_url);
        let authorization_code = query.get("code").expect("code not found in callback URL");

        let access_token = self
            .exchange_authorization_code(metadata.authorization_server(), authorization_code)
            .await;
        assert!(
            !access_token.is_empty(),
            "Failed to exchange authorization code"
        );

        let credential_response = self
            .request_credential(metadata, offer, &access_token)
            .await;
        assert_eq!(
            credential_response.credentials.len(),
            1,
            "Expected 1 credential, got {}",
            credential_response.credentials.len()
        );
        let credential_jwt = &credential_response.credentials[0].credential;
        VerifiableCredential::from_jwt(credential_jwt)
    }

    async fn get_nonce(&self, nonce_endpoint: &str) -> String {
        let response = self
            .http_client
            .post(
                nonce_endpoint,
                None,
                Some(&[("Accept", "application/json")]),
            )
            .await;
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
        let data: serde_json::Value = response.json().await.unwrap();
        data["c_nonce"]
            .as_str()
            .expect("c_nonce not found in response")
            .to_string()
    }

    async fn request_credential(
        &self,
        metadata: &CredentialIssuerMetadata,
        offer: &Offer,
        access_token: &str,
    ) -> CredentialResponse {
        let nonce_endpoint = metadata
            .nonce_endpoint
            .as_ref()
            .expect("nonce_endpoint is not available in metadata, but we require it");
        let nonce = self.get_nonce(nonce_endpoint).await;
        let proof = self.proof(&metadata.credential_issuer, &nonce);

        let body = serde_json::json!({
            "format": "jwt_vc_json",
            "credential_configuration_id": offer.credential_configuration_ids[0],
            "proofs": { "jwt": [proof] },
            "proof": { "proof_type": "jwt", "jwt": proof },
            "issuer_state": offer.issuer_state(),
        });

        let response = self
            .http_client
            .post(
                &metadata.credential_endpoint,
                Some(&body),
                Some(&[
                    ("Content-Type", "application/json"),
                    ("Authorization", &format!("Bearer {access_token}")),
                ]),
            )
            .await;
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
        response.json::<CredentialResponse>().await.unwrap()
    }

    /// Generate an OID4VCI proof JWT signed with the wallet's EdDSA key.
    fn proof(&self, credential_issuer: &str, nonce: &str) -> String {
        let header = jsonwebtoken::Header {
            typ: Some("openid4vci-proof+jwt".to_string()),
            kid: Some(self.did()),
            alg: jsonwebtoken::Algorithm::EdDSA,
            ..Default::default()
        };
        let claims = serde_json::json!({
            "iss": self.client_id,
            "aud": credential_issuer,
            "iat": chrono::Utc::now().timestamp(),
            "nonce": nonce,
        });
        use ed25519_dalek::pkcs8::{DecodePrivateKey, EncodePrivateKey};
        let signing_key = ed25519_dalek::SigningKey::from_pkcs8_pem(&self._private_key())
            .expect("Failed to parse wallet private key");
        let der = signing_key
            .to_pkcs8_der()
            .expect("Failed to encode key as DER");
        let key = jsonwebtoken::EncodingKey::from_ed_der(der.as_bytes());
        jsonwebtoken::encode(&header, &claims, &key).expect("Failed to encode proof JWT")
    }

    /// The wallet's did:jwk, derived from the public key.
    fn did(&self) -> String {
        use ed25519_dalek::pkcs8::DecodePublicKey;
        let verifying_key = ed25519_dalek::VerifyingKey::from_public_key_pem(&self._public_key())
            .expect("Failed to parse wallet public key");
        let jwk = serde_json::json!({
            "kty": "OKP",
            "crv": "Ed25519",
            "x": BASE64URL_NOPAD.encode(verifying_key.as_bytes()),
        });
        format!(
            "did:jwk:{}",
            BASE64URL_NOPAD.encode(jwk.to_string().as_bytes())
        )
    }

    async fn get_offer(&self, offer: &str) -> Offer {
        assert!(
            offer.starts_with("openid-credential-offer://"),
            "Expected offer to start with openid-credential-offer://"
        );
        let query = parse_query(offer);
        let credential_offer_uri = query
            .get("credential_offer_uri")
            .expect("credential_offer_uri not found");

        let response = self.http_client.get(credential_offer_uri, None).await;
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
        response.json::<Offer>().await.unwrap()
    }

    async fn get_issuer_metadata(&self, offer: &Offer) -> CredentialIssuerMetadata {
        let url = format!(
            "{}/.well-known/openid-credential-issuer",
            offer.credential_issuer
        );
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
        response.json().await.unwrap()
    }

    async fn get_auth_metadata(&self, auth_server_url: &str) -> OpenidConfiguration {
        let url = format!("{}/.well-known/oauth-authorization-server", auth_server_url);
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
        response.json().await.unwrap()
    }

    async fn exchange_authorization_code(
        &self,
        auth_server_url: &str,
        authorization_code: &str,
    ) -> String {
        let token_endpoint = format!("{}/auth/token", auth_server_url);
        let data = serde_urlencoded::to_string(serde_json::json!({
            "grant_type": "authorization_code",
            "code": authorization_code,
            "code_verifier": self.code_verifier.clone().unwrap_or_default(),
            "client_id": self.client_id,
            "redirect_uri": self.deeplink,
        }))
        .unwrap();

        let response = self
            .http_client
            .post_form(&token_endpoint, &data, None)
            .await;

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

        let token_resp = response.json::<AccessTokenResponse>().await.unwrap();
        token_resp.access_token
    }

    fn _private_key(&self) -> String {
        std::fs::read_to_string(self.keys_dir.join("wallet_holder_eddsa.priv")).unwrap()
    }

    fn _public_key(&self) -> String {
        std::fs::read_to_string(self.keys_dir.join("wallet_holder_eddsa.pub")).unwrap()
    }
}

fn parse_query(url: &str) -> std::collections::HashMap<String, String> {
    let parsed = url::Url::parse(url).unwrap();
    parsed
        .query_pairs()
        .map(|(k, v)| (k.into_owned(), v.into_owned()))
        .collect()
}
