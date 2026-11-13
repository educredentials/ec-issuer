/// SSI-Agent adapter for offer operations.
use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use crate::awards::models::OB3Award;
use crate::helpers::http_client::HttpClient;
use crate::helpers::http_client::helpers::{
    add_content_type_json, build_url, is_error, parse_json,
};
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
            let ctx_elements = award
                .credential_context
                .as_ref()
                .map_or_default(|c| {
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
            captured
                .parse::<usize>()
                .unwrap_or(0)
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
            &format!("/v0/offers/{offer_id}")
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
