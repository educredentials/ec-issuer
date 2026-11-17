/// SSI-Agent adapter for offer operations.
use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use crate::awards::models::OB3Award;
use crate::helpers::http_client::helpers::{
    add_content_type_json, build_url, is_error, parse_json,
};
use crate::helpers::http_client::HttpClient;
use crate::offers::models::{CredentialType, Offer, OfferCreated};
use crate::offers::port::{OffersClientError, OffersClientPort};

/// The SSI agent requires these 3 base OB3 contexts to appear first
/// in the @context array.
const OB3_BASE_CONTEXTS: [&str; 3] = [
    "https://www.w3.org/ns/credentials/v2",
    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
    "https://purl.imsglobal.org/spec/ob/v3p0/extensions.json",
];

/// Credential offer request payload.
#[derive(Debug, Serialize, Deserialize)]
struct CredentialOffer {
    credential_issuer: String,
    credential_template_id: String,
    grants: HashMap<String, HashMap<String, String>>,
}

/// SSI agent response on fetching a single offer from the admin API.
#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct SsiAgentOfferResponse {
    id: String,
    grant_types: Vec<String>,
    credential_offer_uri: HashMap<String, String>,
    credential_offer: HashMap<String, CredentialOffer>,
    subject_id: Option<String>,
    credential_ids: Vec<String>,
    form_url_encoded_credential_offer: String,
    pre_authorized_code: String,
    credential_response: Option<String>,
    status: String,
    tx_code: Option<String>,
    delivery_options: Option<String>,
}

/// Adapter for SSI Agent offers API.
pub struct SsiAgentOffersClient<C: HttpClient> {
    ssi_agent_admin_base_url: String,
    client: C,
    credential_template_ids: HashMap<CredentialType, String>,
}

impl<C: HttpClient> SsiAgentOffersClient<C> {
    /// Create a new SSI agent offers client.
    ///
    /// # Arguments
    ///
    /// * `ssi_agent_url` - The admin base URL of the SSI agent.
    /// * `credential_template_ids` - The credential template IDs to use for offers.
    /// * `client` - HTTP client implementation.
    pub fn new(
        ssi_agent_url: &str,
        credential_template_ids: HashMap<CredentialType, String>,
        client: C,
    ) -> Self {
        Self {
            ssi_agent_admin_base_url: ssi_agent_url.trim_end_matches('/').to_string(),
            client,
            credential_template_ids,
        }
    }

    /// Assemble the @context for OB3 or EDC credentials.
    fn _assemble_context(
        &self,
        award: &OB3Award,
        credential_type: &str,
        credential: &serde_json::Value,
    ) -> Vec<CredentialContextItem> {
        if credential_type == "ob3" {
            let ctx_elements = award.credential_context.as_ref().map_or_default(|c| {
                c.iter()
                    .map(|item| match item {
                        crate::awards::models::CredentialContextItem::Url(url) => {
                            CredentialContextItem::Url(url.clone())
                        }
                        crate::awards::models::CredentialContextItem::Inline(m) => {
                            CredentialContextItem::Inline(m.clone())
                        }
                    })
                    .collect::<Vec<_>>()
            });

            let mut result = OB3_BASE_CONTEXTS
                .iter()
                .map(|s| CredentialContextItem::Url(s.to_string()))
                .collect::<Vec<_>>();

            let mut extension_urls = Vec::new();
            let mut inline_ctx: Option<HashMap<String, String>> = None;

            for elem in ctx_elements {
                match elem {
                    CredentialContextItem::Url(url) => {
                        if !OB3_BASE_CONTEXTS.iter().any(|&base| base == url) {
                            extension_urls.push(CredentialContextItem::Url(url));
                        }
                    }
                    CredentialContextItem::Inline(m) => {
                        inline_ctx = Some(m);
                    }
                }
            }

            result.extend(extension_urls);
            if let Some(ctx) = inline_ctx {
                result.push(CredentialContextItem::Inline(ctx));
            }

            result
        } else {
            // EDC: hardcoded contexts first, then extension (legacy order)
            let mut result = vec![
                CredentialContextItem::Url("https://www.w3.org/2018/credentials/v1".to_string()),
                CredentialContextItem::Url("https://www.ns/credentials/v2".to_string()),
            ];

            if let Some(credential_context) = credential.get("credential_context") {
                if let Some(ctx_arr) = credential_context.as_array() {
                    for item in ctx_arr {
                        if let Some(url) = item.as_str() {
                            result.push(CredentialContextItem::Url(url.to_string()));
                        }
                    }
                }
            }

            result
        }
    }

    /// Attach credentialStatus derived from the Badgr `entity_id`.
    fn _attach_status_list(&self, entity_id: Option<&str>, credential: &mut serde_json::Value) {
        let Some(entity_id) = entity_id else { return };

        // Extract numeric idx from entity_id URL (e.g. https://host/assertions/3527)
        let idx = if let Some(pos) = entity_id.rfind('/') {
            let captured = &entity_id[pos + 1..];
            captured.parse::<usize>().unwrap_or(0)
        } else {
            return;
        };

        let status_base = &self.ssi_agent_admin_base_url;
        let status_list = serde_json::json!({
            "id": format!("{}#{}", entity_id, idx),
            "type": "statuslist+jwt",
            "idx": idx,
            "uri": format!("{}/v0/status/{}", status_base, idx),
        });

        credential["credentialStatus"] = status_list;
    }

    /// POST credential to SSI agent (/v0/credentials).
    ///
    /// # Errors
    ///
    /// Returns `OffersClientError` on failure.
    fn _post_credential(
        &self,
        offer_id: &str,
        credential: &serde_json::Value,
        template_id: &str,
    ) -> Result<String, OffersClientError> {
        let url = build_url(&self.ssi_agent_admin_base_url, "/v0/credentials");
        let body = serde_json::json!({
            "offerId": offer_id,
            "credential": credential,
            "templateId": template_id,
            "expiresAt": "never",
        });

        let mut headers = HashMap::new();
        add_content_type_json(&mut headers);

        let response = self.client.post(&url, &headers, &body.to_string())?;

        if is_error(response.status_code) {
            return Err(OffersClientError(
                crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            ));
        }

        // Try 1: Location header — parse credential ID from path
        if let Some(location) = response.headers.get("Location") {
            if let Some(pos) = location.rfind('/') {
                let id = &location[pos + 1..];
                if !id.is_empty() {
                    return Ok(id.to_string());
                }
            }
        }

        // Try 2: JSON body — credential ID as top-level string or in "id" field
        if let Ok(body_map) =
            serde_json::from_slice::<HashMap<String, serde_json::Value>>(&response.content)
        {
            if let Some(id) = body_map.get("id") {
                return Ok(id.to_string());
            }
        }

        // Try 3: Raw text as the credential ID
        Ok(response.text().trim().trim_matches('"').to_string())
    }

    /// POST offer to SSI agent (/v0/offers).
    fn _post_offer(
        &self,
        offer_id: &str,
        template_ids: &[String],
    ) -> Result<OfferCreated, OffersClientError> {
        let url = build_url(&self.ssi_agent_admin_base_url, "/v0/offers");
        let body = serde_json::json!({
            "offerId": offer_id,
            "templateIds": template_ids,
        });

        let mut headers = HashMap::new();
        add_content_type_json(&mut headers);

        let response = self.client.post(&url, &headers, &body.to_string())?;

        if is_error(response.status_code) {
            return Err(OffersClientError(
                crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            ));
        }

        let uri = response.text().trim().to_string();
        Ok(OfferCreated {
            uri,
            credential_ids: None,
        })
    }
}

impl<C: HttpClient> OffersClientPort for SsiAgentOffersClient<C> {
    fn create_ob3(
        &self,
        offer_id: &str,
        award: &OB3Award,
    ) -> Result<OfferCreated, OffersClientError> {
        let mut credential = serde_json::to_value(award)
            .map_err(|e| OffersClientError(format!("Failed to serialize OB3 award: {e}")))?;

        // Assemble and attach @context
        let context = self._assemble_context(award, "ob3", &credential);
        credential["credential_context"] = serde_json::to_value(&context)
            .map_err(|e| OffersClientError(format!("Failed to serialize context: {e}")))?;

        // Remove internal fields
        if let Some(o) = credential.as_object_mut() {
            o.remove("credential_context");
            o.remove("entity_id");
        }

        // Attach status list
        self._attach_status_list(award.entity_id.as_deref(), &mut credential);

        let template_id = self
            .credential_template_ids
            .get(&CredentialType::OB3)
            .cloned()
            .unwrap_or_default();

        let _credential_ids = self._post_credential(offer_id, &credential, &template_id)?;
        self._post_offer(offer_id, &[template_id])
    }

    fn create_edc(
        &self,
        offer_id: &str,
        credential: &serde_json::Value,
    ) -> Result<OfferCreated, OffersClientError> {
        let mut credential = credential.clone();

        // Assemble and attach @context for EDC
        let context = self._assemble_context(
            &OB3Award {
                id: String::new(),
                r#type: vec![],
                name: String::new(),
                issuer: crate::awards::models::Issuer {
                    id: String::new(),
                    name: String::new(),
                    r#type: vec![],
                    parent_org: None,
                },
                valid_from: String::new(),
                credential_subject: crate::awards::models::AchievementSubject {
                    id: String::new(),
                    r#type: vec![],
                    achievement: crate::awards::models::Achievement {
                        id: String::new(),
                        r#type: vec![],
                        criteria: crate::awards::models::Criteria::default(),
                        description: String::new(),
                        name: String::new(),
                        image: None,
                        in_language: None,
                        ects: None,
                        eqf: None,
                        learning_outcome: None,
                        education_program_identifier: None,
                        form_of_participation: None,
                        assessment_type: None,
                        supervision_type: None,
                        time_investment: None,
                    },
                    identifier: vec![],
                },
                credential_schema: vec![],
                valid_until: None,
                entity_id: None,
                credential_context: None,
                credential_status: None,
            },
            "edc",
            &credential,
        );
        credential["credential_context"] = serde_json::to_value(&context)
            .map_err(|e| OffersClientError(format!("Failed to serialize context: {e}")))?;

        let template_id = self
            .credential_template_ids
            .get(&CredentialType::EDC)
            .cloned()
            .unwrap_or_default();

        let credential_ids = self._post_credential(offer_id, &credential, &template_id)?;
        self._post_offer(offer_id, &[template_id])
            .map(|oc| OfferCreated {
                credential_ids: Some(vec![credential_ids]),
                ..oc
            })
    }

    fn get(&self, offer_id: &str) -> Result<Offer, OffersClientError> {
        let url = build_url(
            &self.ssi_agent_admin_base_url,
            &format!("/v0/offers/{offer_id}"),
        );
        let response = self.client.get(&url, &HashMap::new())?;

        if response.status_code == 404 {
            return Err(OffersClientError(format!("Offer {offer_id} not found")));
        }

        if is_error(response.status_code) {
            return Err(OffersClientError(
                crate::helpers::http_client::helpers::build_error_body(
                    response.status_code,
                    &response,
                ),
            ));
        }

        let response_data = parse_json::<SsiAgentOfferResponse>(&response)?;

        Ok(Offer {
            offer_id: offer_id.to_string(),
            award_id: String::new(),
            uri: Some(response_data.form_url_encoded_credential_offer),
            credential_ids: response_data.credential_ids,
            created_at: None,
        })
    }

    fn rollback(&self, _offer_id: &str) -> Result<(), OffersClientError> {
        // The SSI agent does not expose a delete endpoint for credentials or
        // offers, so this is a no-op.
        Ok(())
    }
}

/// A single item in the @context array.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
enum CredentialContextItem {
    Url(String),
    Inline(HashMap<String, String>),
}

/// Convenience constructor for the Arc-wrapped client type.
///
/// Returns `SsiAgentOffersClient<ReqwestHttpClientArc>` for use with axum's
/// `'static` state requirements.
#[must_use]
#[allow(clippy::implicit_hasher)]
pub fn new_ssi_agent_offers_client_arc(
    ssi_agent_url: &str,
    credential_template_ids: HashMap<CredentialType, String>,
    client: &crate::helpers::reqwest_client::ReqwestHttpClientArc,
) -> SsiAgentOffersClient<crate::helpers::reqwest_client::ReqwestHttpClientArc> {
    SsiAgentOffersClient::new(ssi_agent_url, credential_template_ids, client.clone())
}

#[cfg(test)]
mod tests {
    use std::collections::HashMap;
    use std::sync::Mutex;

    use crate::awards::models::CredentialContextItem as AwardContextItem;
    use crate::helpers::http_client::{HttpClientError, HttpResponse};

    use super::*;

    struct TestClient {
        get_status: Option<u16>,
        get_body: Option<Vec<u8>>,
        post_responses: Mutex<Vec<(u16, Vec<u8>, HashMap<String, String>)>>,
    }

    impl TestClient {
        fn with_post_ok(status: u16, body: &[u8]) -> Self {
            Self {
                get_status: None,
                get_body: None,
                post_responses: Mutex::new(vec![(status, body.to_vec(), HashMap::new())]),
            }
        }

        fn with_post_ok_headers(
            status: u16,
            body: &[u8],
            headers: HashMap<String, String>,
        ) -> Self {
            Self {
                get_status: None,
                get_body: None,
                post_responses: Mutex::new(vec![(status, body.to_vec(), headers)]),
            }
        }

        fn with_post_ok_seq(responses: Vec<(u16, Vec<u8>, HashMap<String, String>)>) -> Self {
            Self {
                get_status: None,
                get_body: None,
                post_responses: Mutex::new(responses),
            }
        }
    }

    impl HttpClient for TestClient {
        fn get(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            match (self.get_status, self.get_body.as_ref()) {
                (Some(s), Some(b)) => Ok(HttpResponse {
                    status_code: s,
                    url: "http://mock".to_string(),
                    headers: HashMap::new(),
                    content: b.clone(),
                }),
                _ => Err(HttpClientError::Connection("not configured".to_string())),
            }
        }

        fn post(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            let mut responses = self.post_responses.lock().unwrap();
            if responses.is_empty() {
                return Err(HttpClientError::Connection(
                    "no more post responses configured".to_string(),
                ));
            }
            let (status, body, headers) = responses.remove(0);
            Ok(HttpResponse {
                status_code: status,
                url: "http://mock".to_string(),
                headers,
                content: body,
            })
        }

        fn delete(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }

        fn patch(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
    }

    fn sample_ob3_award() -> OB3Award {
        let mut ctx_map = HashMap::new();
        ctx_map.insert("key".to_string(), "value".to_string());

        OB3Award {
            id: "award-1".to_string(),
            r#type: vec!["Claim".to_string()],
            name: "Test Award".to_string(),
            issuer: crate::awards::models::Issuer {
                id: "issuer-1".to_string(),
                name: "Test Org".to_string(),
                r#type: vec!["Organization".to_string()],
                parent_org: None,
            },
            valid_from: "2024-01-01".to_string(),
            credential_subject: crate::awards::models::AchievementSubject {
                id: "subject-1".to_string(),
                r#type: vec!["AchievementSubject".to_string()],
                achievement: crate::awards::models::Achievement {
                    id: "achievement-1".to_string(),
                    r#type: vec!["Achievement".to_string()],
                    criteria: crate::awards::models::Criteria {
                        narrative: "Test criteria".to_string(),
                    },
                    description: "Test".to_string(),
                    name: "Test".to_string(),
                    image: None,
                    in_language: None,
                    ects: None,
                    eqf: None,
                    learning_outcome: None,
                    education_program_identifier: None,
                    form_of_participation: None,
                    assessment_type: None,
                    supervision_type: None,
                    time_investment: None,
                },
                identifier: vec![],
            },
            credential_schema: vec![],
            valid_until: None,
            entity_id: Some("https://host/assertions/3527".to_string()),
            credential_context: Some(vec![
                AwardContextItem::Url("https://example.com/ext.json".to_string()),
                AwardContextItem::Inline(ctx_map),
            ]),
            credential_status: None,
        }
    }

    #[test]
    fn test_assemble_context_ob3_includes_base_contexts() {
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let award = sample_ob3_award();
        let context = client._assemble_context(&award, "ob3", &serde_json::json!({}));
        assert!(context.len() >= 3);
    }

    #[test]
    fn test_assemble_context_ob3_filters_base_urls() {
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut award = sample_ob3_award();
        if let Some(ref mut ctx) = award.credential_context {
            ctx.push(AwardContextItem::Url(
                "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json".to_string(),
            ));
        }
        let context = client._assemble_context(&award, "ob3", &serde_json::json!({}));
        let base_url = "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json";
        let count = context
            .iter()
            .filter(|item| {
                if let CredentialContextItem::Url(url) = item {
                    url == base_url
                } else {
                    false
                }
            })
            .count();
        assert_eq!(count, 1);
    }

    #[test]
    fn test_assemble_context_includes_non_base_urls() {
        // Catches the == → != mutant at line 110:71
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut award = sample_ob3_award();
        if let Some(ref mut ctx) = award.credential_context {
            ctx.push(AwardContextItem::Url(
                "https://example.com/unique-extension.json".to_string(),
            ));
        }
        let context = client._assemble_context(&award, "ob3", &serde_json::json!({}));
        let has_unique = context.iter().any(|item| {
            if let CredentialContextItem::Url(url) = item {
                url == "https://example.com/unique-extension.json"
            } else {
                false
            }
        });
        assert!(
            has_unique,
            "non-base extension URL should appear in context"
        );
    }

    #[test]
    fn test_assemble_context_ob3_without_credential_context() {
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut award = sample_ob3_award();
        award.credential_context = None;
        let context = client._assemble_context(&award, "ob3", &serde_json::json!({}));
        assert_eq!(context.len(), 3);
    }

    #[test]
    fn test_post_credential_returns_id_from_raw_body() {
        let mock = TestClient::with_post_ok(201, b"cred-42");
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        let result = client._post_credential("offer-1", &serde_json::json!({}), "tmpl-1");
        assert_eq!(result.unwrap(), "cred-42");
    }

    #[test]
    fn test_post_credential_returns_id_from_location_header() {
        // Catches the + → -/* mutants at line 208:40
        let mut headers = HashMap::new();
        headers.insert(
            "Location".to_string(),
            "/v0/credentials/cred-42".to_string(),
        );
        let mock = TestClient::with_post_ok_headers(201, b"", headers);
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        let result = client._post_credential("offer-1", &serde_json::json!({}), "tmpl-1");
        assert_eq!(result.unwrap(), "cred-42");
    }

    #[test]
    fn test_post_credential_returns_id_from_body_map() {
        let body = serde_json::json!({"id": "cred-from-body"});
        let mock = TestClient::with_post_ok(201, body.to_string().into_bytes().as_slice());
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        let result = client._post_credential("offer-1", &serde_json::json!({}), "tmpl-1");
        assert_eq!(result.unwrap(), "\"cred-from-body\"");
    }

    #[test]
    fn test_post_credential_error_on_400() {
        let mock = TestClient::with_post_ok(400, b"Bad request");
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        match client._post_credential("offer-1", &serde_json::json!({}), "tmpl-1") {
            Err(OffersClientError(msg)) => assert!(msg.contains("400")),
            Ok(_) => panic!("expected error on 400"),
        }
    }

    #[test]
    fn test_post_credential_error_on_500() {
        let mock = TestClient::with_post_ok(500, b"Internal server error");
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        match client._post_credential("offer-1", &serde_json::json!({}), "tmpl-1") {
            Err(OffersClientError(msg)) => assert!(msg.contains("500")),
            Ok(_) => panic!("expected error on 500"),
        }
    }

    #[test]
    fn test_post_credential_error_on_404() {
        // Catches the delete ! mutant at line 209:20
        let mock = TestClient::with_post_ok(404, b"Not found");
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        match client._post_credential("offer-1", &serde_json::json!({}), "tmpl-1") {
            Err(OffersClientError(msg)) => assert!(msg.contains("404")),
            Ok(_) => panic!("expected error on 404"),
        }
    }

    #[test]
    fn test_create_ob3_posts_credential_and_offer() {
        let mock = TestClient::with_post_ok_seq(vec![(201, b"cred-1".to_vec(), HashMap::new())]);
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::from_iter([(CredentialType::OB3, "tmpl-1".to_string())]),
            mock,
        );
        let award = sample_ob3_award();
        match client.create_ob3("offer-1", &award) {
            Err(OffersClientError(msg)) => {
                assert!(!msg.contains("serialize"));
            }
            Ok(_) => panic!("expected error from second POST"),
        }
    }

    #[test]
    fn test_create_edc_sets_credential_ids() {
        // Catches the delete credential_ids field mutant at line 358:17
        // FIFO: first _post_credential, second _post_offer
        let mock = TestClient::with_post_ok_seq(vec![
            (201, b"cred-edc".to_vec(), HashMap::new()),
            (201, b"http://mock/offer/offer-1".to_vec(), HashMap::new()),
        ]);
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::from_iter([
                (CredentialType::OB3, "tmpl-ob3".to_string()),
                (CredentialType::EDC, "tmpl-edc".to_string()),
            ]),
            mock,
        );
        let credential = serde_json::json!({"type": "VerifiableCredential"});
        let result = client.create_edc("offer-1", &credential);
        assert!(result.is_ok());
        let offer = result.unwrap();
        assert!(
            offer.credential_ids.is_some(),
            "credential_ids should be Some"
        );
        assert_eq!(
            offer.credential_ids.as_ref().unwrap(),
            &vec!["cred-edc".to_string()]
        );
    }

    #[test]
    fn test_create_edc_sets_credential_ids_on_error() {
        let mock = TestClient::with_post_ok_seq(vec![(201, b"cred-edc".to_vec(), HashMap::new())]);
        let client = SsiAgentOffersClient::new(
            "http://mock",
            HashMap::from_iter([
                (CredentialType::OB3, "tmpl-ob3".to_string()),
                (CredentialType::EDC, "tmpl-edc".to_string()),
            ]),
            mock,
        );
        let credential = serde_json::json!({"type": "VerifiableCredential"});
        match client.create_edc("offer-1", &credential) {
            Err(OffersClientError(msg)) => {
                assert!(!msg.contains("serialize"));
            }
            Ok(_) => panic!("expected error from second POST"),
        }
    }

    #[test]
    fn test_attach_status_list_simple_entity_id() {
        let client = SsiAgentOffersClient::new(
            "http://localhost:8001",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut credential = serde_json::json!({"type": "VerifiableCredential"});
        client._attach_status_list(Some("https://host/assertions/3527"), &mut credential);
        assert!(credential.get("credentialStatus").is_some());
        assert_eq!(
            credential["credentialStatus"]["idx"].as_u64().unwrap(),
            3527
        );
    }

    #[test]
    fn test_attach_status_list_no_slash_returns_empty() {
        let client = SsiAgentOffersClient::new(
            "http://localhost:8001",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut credential = serde_json::json!({"type": "VerifiableCredential"});
        client._attach_status_list(Some("no_slash_here"), &mut credential);
        assert!(credential.get("credentialStatus").is_none());
    }

    #[test]
    fn test_attach_status_list_no_entity_id() {
        let client = SsiAgentOffersClient::new(
            "http://localhost:8001",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut credential = serde_json::json!({"type": "VerifiableCredential"});
        client._attach_status_list(None, &mut credential);
        assert!(credential.get("credentialStatus").is_none());
    }

    #[test]
    fn test_attach_status_list_non_numeric_idx_defaults_to_zero() {
        let client = SsiAgentOffersClient::new(
            "http://localhost:8001",
            HashMap::new(),
            TestClient::with_post_ok(200, b"{}"),
        );
        let mut credential = serde_json::json!({"type": "VerifiableCredential"});
        client._attach_status_list(Some("https://host/assertions/abc"), &mut credential);
        assert!(credential.get("credentialStatus").is_some());
        assert_eq!(credential["credentialStatus"]["idx"].as_u64().unwrap(), 0);
    }

    #[test]
    fn test_get_returns_offer_on_success() {
        let body = serde_json::json!({
            "id": "offer-1",
            "grant_types": [],
            "credential_offer_uri": {},
            "credential_offer": {},
            "credential_ids": ["cred-1"],
            "form_url_encoded_credential_offer": "offer=encoded",
            "pre_authorized_code": "",
            "status": "pending"
        });
        let mock = GetClient {
            status: 200,
            body: body.to_string().into_bytes(),
        };
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        let result = client.get("offer-1");
        assert!(result.is_ok());
        let offer = result.unwrap();
        assert_eq!(offer.offer_id, "offer-1");
        assert_eq!(offer.uri, Some("offer=encoded".to_string()));
        assert_eq!(offer.credential_ids, vec!["cred-1".to_string()]);
    }

    #[test]
    fn test_get_returns_error_on_404() {
        let mock = GetClient {
            status: 404,
            body: b"Not found".to_vec(),
        };
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        assert!(client.get("offer-1").is_err());
    }

    #[test]
    fn test_rollback_is_noop() {
        let mock = TestClient::with_post_ok(200, b"{}");
        let client = SsiAgentOffersClient::new("http://mock", HashMap::new(), mock);
        assert!(client.rollback("offer-1").is_ok());
    }

    struct GetClient {
        status: u16,
        body: Vec<u8>,
    }

    impl HttpClient for GetClient {
        fn get(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            Ok(HttpResponse {
                status_code: self.status,
                url: "http://mock".to_string(),
                headers: HashMap::new(),
                content: self.body.clone(),
            })
        }
        fn post(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn delete(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
        fn patch(
            &self,
            _url: &str,
            _headers: &HashMap<String, String>,
            _body: &str,
        ) -> Result<HttpResponse, HttpClientError> {
            Err(HttpClientError::Connection("not configured".to_string()))
        }
    }
}
