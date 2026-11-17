/// Badgr DTOs and mapping to OB3 award domain model.
use crate::awards::badgr_dtos::BadgrAwardResponse;
use crate::awards::badgr_extensions;

pub use crate::awards::badgr_dtos::AwardMappingError;

use crate::awards::models::{
    ob3_default_schema, Achievement, AchievementSubject, Address, Criteria, IdentifierEntry,
    IdentityObject, Issuer, OB3Award, ParentOrg,
};
use crate::offers::models::CredentialType;
use std::collections::HashMap;

// ─── Public API ─────────────────────────────────────────────────────────────

/// Convert Badgr API JSON response to OB3 Award domain model.
///
/// # Arguments
///
/// * `raw` - The parsed JSON response from the Badgr awards API.
/// * `award_base_url` - Optional base URL to resolve relative image paths.
/// * `issuer_base_url` - Optional base URL for credential context URLs.
/// * `extensions_url_prefix` - URL prefix for extensions (default: "/static/extensions/v1").
///
/// # Returns
///
/// A fully-structured OB3 Award.
///
/// # Errors
///
/// Returns `AwardMappingError` when the response is missing required fields.
pub fn ob3_award_from_badgr_api_response(
    raw: &serde_json::Value,
    award_base_url: Option<&str>,
    issuer_base_url: Option<&str>,
    extensions_url_prefix: Option<&str>,
) -> Result<OB3Award, AwardMappingError> {
    let dto = BadgrAwardResponse::from_json(raw)
        .map_err(|e| AwardMappingError(format!("failed to parse badgr response: {e}")))?;

    _to_ob3_award(&dto, award_base_url, issuer_base_url, extensions_url_prefix)
}

// ─── Mapping logic ──────────────────────────────────────────────────────────

fn _to_ob3_award(
    dto: &BadgrAwardResponse,
    award_base_url: Option<&str>,
    issuer_base_url: Option<&str>,
    extensions_url_prefix: Option<&str>,
) -> Result<OB3Award, AwardMappingError> {
    let credential_id = _resolve_credential_id(dto)?;
    let badge_name = _resolve_badge_name(dto);
    let issuer = _resolve_issuer(dto);
    let valid_from = _resolve_valid_from(dto);
    let achievement_data = _resolve_achievement_data(dto);
    let identifier = _resolve_identifier(dto);
    let image = _resolve_image(dto, award_base_url);

    let valid_to = dto.expires_at.clone();
    let badgeclass = &dto.badgeclass;

    let ext_vals = badgr_extensions::_extract_extension_values(badgeclass.as_ref());

    let base_url = issuer_base_url.unwrap_or("http://localhost:8000");
    let ext_prefix = extensions_url_prefix.unwrap_or("/static/extensions/v1");
    let credential_context = badgr_extensions::_credential_context_urls(
        base_url,
        ext_prefix,
        &ext_vals,
        Some(CredentialType::OB3),
    );

    Ok(OB3Award {
        id: credential_id.clone(),
        r#type: vec![
            "VerifiableCredential".to_string(),
            "AchievementCredential".to_string(),
        ],
        name: badge_name.clone(),
        issuer,
        valid_from,
        valid_until: valid_to,
        credential_subject: AchievementSubject {
            id: credential_id.clone(),
            r#type: vec!["AchievementSubject".to_string()],
            achievement: Achievement {
                id: credential_id,
                r#type: vec!["Achievement".to_string()],
                criteria: Criteria {
                    narrative: achievement_data["criteria_text"].clone(),
                },
                description: achievement_data["description"].clone(),
                name: badge_name,
                image,
                in_language: ext_vals.in_language.clone(),
                ects: ext_vals.ects.clone(),
                eqf: ext_vals.eqf.clone(),
                learning_outcome: ext_vals.learning_outcome.clone(),
                education_program_identifier: ext_vals.education_program_identifier.clone(),
                form_of_participation: ext_vals.participation.clone(),
                assessment_type: ext_vals.assessment_type.clone().map(|t| t.join(",")),
                supervision_type: ext_vals.supervision_type.clone(),
                time_investment: ext_vals
                    .time_investment
                    .as_ref()
                    .and_then(|t| t.parse().ok()),
            },
            identifier,
        },
        credential_schema: ob3_default_schema(),
        credential_context,
        credential_status: None,
        entity_id: dto.entity_id.clone(),
    })
}

fn _resolve_credential_id(dto: &BadgrAwardResponse) -> Result<String, AwardMappingError> {
    dto.entity_id
        .clone()
        .ok_or_else(|| AwardMappingError("badgr award response is missing 'id'".to_string()))
}

fn _resolve_badge_name(dto: &BadgrAwardResponse) -> String {
    if let Some(ref name) = dto.name {
        return name.clone();
    }
    if let Some(ref badgeclass) = dto.badgeclass {
        if !badgeclass.name.is_empty() {
            return badgeclass.name.clone();
        }
    }
    String::new()
}

fn _resolve_valid_from(dto: &BadgrAwardResponse) -> String {
    dto.issued_on.clone().unwrap_or_default()
}

fn _resolve_image(
    dto: &BadgrAwardResponse,
    base_url: Option<&str>,
) -> Option<HashMap<String, String>> {
    let raw_image = dto.badgeclass.as_ref().and_then(|b| b.image.clone());
    let raw_image = raw_image?;

    let image_id = match base_url {
        Some(base) if !raw_image.starts_with("http://") && !raw_image.starts_with("https://") => {
            format!("{}{}", base.trim_end_matches('/'), raw_image)
        }
        _ => raw_image,
    };

    let mut map = HashMap::new();
    map.insert("id".to_string(), image_id);
    map.insert("type".to_string(), "Image".to_string());
    Some(map)
}

fn _resolve_identifier(dto: &BadgrAwardResponse) -> Vec<IdentityObject> {
    let mut identifiers = Vec::new();

    if let Some(ref email) = dto.email {
        identifiers.push(IdentityObject {
            r#type: "IdentityObject".to_string(),
            identity_hash: email.clone(),
            identity_type: "emailAddress".to_string(),
            hashed: false,
        });
    }

    let name = _resolve_name(dto);
    if !name.is_empty() {
        identifiers.push(IdentityObject {
            r#type: "IdentityObject".to_string(),
            identity_hash: name,
            identity_type: "name".to_string(),
            hashed: false,
        });
    }

    identifiers
}

fn _resolve_name(dto: &BadgrAwardResponse) -> String {
    let parts: Vec<&str> = dto
        .given_name
        .as_deref()
        .into_iter()
        .chain(dto.family_name.as_deref())
        .filter(|s| !s.is_empty())
        .collect();
    parts.join(" ")
}

fn _resolve_achievement_data(dto: &BadgrAwardResponse) -> HashMap<String, String> {
    let mut data = HashMap::new();
    let mut criteria_text = String::new();
    let mut description = String::new();

    if let Some(ref badgeclass) = dto.badgeclass {
        if let Some(ref criteria) = badgeclass.criteria {
            if let Some(ref narrative) = criteria.narrative {
                criteria_text.clone_from(narrative);
            }
        }
        if criteria_text.is_empty() {
            if let Some(ref text) = badgeclass.criteria_text {
                criteria_text.clone_from(text);
            }
        }
        if let Some(ref desc) = badgeclass.description {
            description.clone_from(desc);
        }
    }

    data.insert("criteria_text".to_string(), criteria_text);
    data.insert("description".to_string(), description);
    data
}

fn _resolve_issuer(dto: &BadgrAwardResponse) -> Issuer {
    let badgeclass = &dto.badgeclass;
    let mut issuer_id = String::new();
    let mut issuer_name = String::new();
    let mut issuer_type: Vec<String> = vec!["Profile".to_string()];

    if let Some(bc) = badgeclass {
        if let Some(ref issuer) = bc.issuer {
            issuer_id = issuer.entity_id.clone().unwrap_or_default();
            issuer_name = issuer.name_english.clone().unwrap_or_default();
            if let Some(ref r#type) = issuer.r#type {
                issuer_type = vec![r#type.clone()];
            }
        }
        if issuer_name.is_empty() {
            issuer_name.clone_from(&bc.name);
        }

        if let Some(ref faculty) = bc.issuer.as_ref().and_then(|i| i.faculty.clone()) {
            if let Some(ref institution) = faculty.institution {
                let inst_name = institution
                    .name_english
                    .clone()
                    .or_else(|| institution.name_dutch.clone())
                    .unwrap_or_default();
                let inst_id = faculty.entity_id.clone().unwrap_or_default();

                let address = institution.country_code.as_ref().map(|cc| Address {
                    address_country_code: Some(cc.clone()),
                    r#type: vec!["Address".to_string()],
                });

                let mut other_idents = Vec::new();
                if let Some(ref brin) = institution.brin {
                    other_idents.push(IdentifierEntry {
                        identifier: brin.clone(),
                        identifier_type: "ext:BRIN".to_string(),
                        r#type: "IdentifierEntry".to_string(),
                    });
                }
                if let Some(ref identifier) = institution.identifier {
                    other_idents.push(IdentifierEntry {
                        identifier: identifier.clone(),
                        identifier_type: "ext:SCHAC".to_string(),
                        r#type: "IdentifierEntry".to_string(),
                    });
                }

                let parent_org = ParentOrg {
                    id: inst_id,
                    name: inst_name,
                    r#type: vec!["Profile".to_string()],
                    address,
                    other_identifier: other_idents,
                };

                return Issuer {
                    id: issuer_id,
                    name: issuer_name,
                    r#type: issuer_type,
                    parent_org: Some(parent_org),
                };
            }
        }
    }

    Issuer {
        id: issuer_id,
        name: issuer_name,
        r#type: issuer_type,
        parent_org: None,
    }
}

// ─── Test helpers ───────────────────────────────────────────────────────────

/// Shared test fixture: builds a minimal badgeclass JSON value.
#[cfg(test)]
#[allow(clippy::needless_pass_by_value)]
fn default_badgeclass(
    participation: Option<Vec<String>>,
    assessment_type: Option<Vec<String>>,
    language: Option<String>,
    ects: Option<String>,
    time_investment: Option<f64>,
    issuer_type: Option<String>,
) -> serde_json::Value {
    serde_json::json!({
        "name": "Badge",
        "entity_id": "https://DOMAIN/badges/1",
        "issuer": {
            "entity_id": "https://DOMAIN/issuers/1",
            "name_english": "Issuer",
            "faculty": null,
            "type": issuer_type,
        },
        "participation": participation,
        "assessment_type": assessment_type,
        "language": language,
        "ects": ects.map(|v| serde_json::json!(v)),
        "time_investment": time_investment,
    })
}

// ─── Tests ──────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    pub mod extension;
    pub mod mapping;
}
