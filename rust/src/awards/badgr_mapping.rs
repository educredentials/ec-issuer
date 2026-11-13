/// Badgr DTOs and mapping to OB3 award domain model.
use crate::awards::models::{
    Achievement,
    AchievementSubject,
    Address,
    Criteria,
    CredentialContextItem,
    IdentityObject,
    IdentifierEntry,
    Issuer,
    OB3Award,
    ParentOrg,
    ob3_default_schema,
};
use crate::offers::models::CredentialType;

use std::collections::HashMap;

/// Error raised when a Badgr award response cannot be mapped to an OB3 award.
#[derive(Debug, thiserror::Error)]
#[error("Badgr mapping error: {0}")]
pub struct AwardMappingError(pub String);

/// Faculty within issuer.
#[allow(dead_code)]
#[derive(Debug, Default, Clone, serde::Deserialize)]
struct BadgrFaculty {
    entity_id: Option<String>,
    name_dutch: Option<String>,
    name_english: Option<String>,
    image_dutch: Option<String>,
    image_english: Option<String>,
    on_behalf_of: Option<serde_json::Value>,
    on_behalf_of_display_name: Option<String>,
    on_behalf_of_url: Option<String>,
    institution: Option<BadgrInstitution>,
}

/// Institution within faculty.
#[allow(dead_code)]
#[derive(Debug, Default, Clone, serde::Deserialize)]
struct BadgrInstitution {
    entity_id: Option<String>,
    name_dutch: Option<String>,
    name_english: Option<String>,
    image_dutch: Option<String>,
    image_english: Option<String>,
    identifier: Option<String>,
    alternative_identifier: Option<String>,
    country_code: Option<String>,
    brin: Option<String>,
}

/// Issuer within badgeclass.
#[allow(dead_code)]
#[derive(Debug, Default, serde::Deserialize)]
struct BadgrIssuer {
    entity_id: Option<String>,
    name_dutch: Option<String>,
    name_english: Option<String>,
    faculty: Option<BadgrFaculty>,
    r#type: Option<String>,
}

/// Criteria inside badgeclass.
#[derive(Debug, Default, serde::Deserialize)]
struct BadgrCriteria {
    narrative: Option<String>,
}

/// Badgeclass extensions extracted from flat fields.
#[derive(Debug, Default, serde::Deserialize)]
struct BadgeclassExtensions {
    in_language: Option<String>,
    ects: Option<String>,
    eqf: Option<String>,
    learning_outcome: Option<String>,
    education_program_identifier: Option<Vec<String>>,
    time_investment: Option<String>,
    supervision_type: Option<String>,
    assessment_type: Option<Vec<String>>,
    participation: Option<Vec<String>>,
}

/// Badgeclass.
#[allow(dead_code)]
#[derive(Debug, Default, serde::Deserialize)]
struct BadgrBadgeclass {
    name: String,
    entity_id: Option<String>,
    description: Option<String>,
    criteria_text: Option<String>,
    image: Option<String>,
    criteria: Option<BadgrCriteria>,
    issuer: Option<BadgrIssuer>,
    eqf: Option<serde_json::Value>,
    ects: Option<serde_json::Value>,
    language: Option<String>,
    learning_outcome: Option<String>,
    time_investment: Option<f64>,
    education_program_identifier: Option<serde_json::Value>,
    participation: Option<Vec<String>>,
    assessment_type: Option<Vec<String>>,
    assessment_id_verified: Option<bool>,
    assessment_supervised: Option<bool>,
    supervision_type: Option<String>,
}

/// Badgr awards API response.
#[allow(dead_code)]
#[derive(Debug, Default, serde::Deserialize)]
struct BadgrAwardResponse {
    entity_id: Option<String>,
    name: Option<String>,
    issued_on: Option<String>,
    image: Option<String>,
    badgeclass: Option<BadgrBadgeclass>,
    given_name: Option<String>,
    family_name: Option<String>,
    email: Option<String>,
    expires_at: Option<String>,
    language: Option<String>,
    ects: Option<serde_json::Value>,
    eqf: Option<serde_json::Value>,
    participation: Option<Vec<String>>,
    assessment_type: Option<Vec<String>>,
    assessment_id_verified: Option<bool>,
    assessment_supervised: Option<bool>,
    learning_outcome: Option<String>,
    education_program_identifier: Option<serde_json::Value>,
    time_investment: Option<f64>,
}

impl BadgrAwardResponse {
    fn from_json(json: &serde_json::Value) -> Result<Self, serde_json::Error> {
        serde_json::from_value(json.clone())
    }
}

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
        .map_err(|e| AwardMappingError(format!("Failed to parse Badgr response: {e}")))?;

    _to_ob3_award(&dto, award_base_url, issuer_base_url, extensions_url_prefix)
}

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

    let ext_vals = _extract_extension_values(badgeclass.as_ref());

    let base_url = issuer_base_url.unwrap_or("http://localhost:8000");
    let ext_prefix = extensions_url_prefix.unwrap_or("/static/extensions/v1");
    let credential_context = _credential_context_urls(base_url, ext_prefix, &ext_vals, None);

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
        .ok_or_else(|| AwardMappingError("Badgr award response is missing 'id'".to_string()))
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

fn _extract_extension_values(badgeclass: Option<&BadgrBadgeclass>) -> BadgeclassExtensions {
    let Some(bc) = badgeclass else { return BadgeclassExtensions::default() };

    BadgeclassExtensions {
        in_language: bc.language.clone(),
        ects: bc
            .ects
            .as_ref()
            .and_then(|v| v.as_str().map(std::string::ToString::to_string)),
        eqf: bc
            .eqf
            .as_ref()
            .and_then(|v| v.as_str().map(std::string::ToString::to_string)),
        learning_outcome: bc.learning_outcome.clone(),
        education_program_identifier: bc.education_program_identifier.as_ref().and_then(|v| {
            v.as_array().map(|arr| {
                arr.iter()
                    .filter_map(|val| val.as_str().map(String::from))
                    .collect()
            })
        }),
        time_investment: bc.time_investment.map(|t| t.to_string()),
        supervision_type: bc.supervision_type.clone(),
        assessment_type: bc.assessment_type.clone(),
        participation: bc.participation.clone(),
    }
}

fn _credential_context_urls(
    issuer_base_url: &str,
    extensions_url_prefix: &str,
    ext_vals: &BadgeclassExtensions,
    _credential_type: Option<CredentialType>,
) -> Option<Vec<CredentialContextItem>> {
    // Build list of extension context URLs with non-null field values
    let ext_map: Vec<(&str, bool)> = vec![
        (
            "LearningOutcomeExtension/context.json",
            ext_vals.learning_outcome.is_some(),
        ),
        ("ECTSExtension/context.json", ext_vals.ects.is_some()),
        ("EQFExtension/context.json", ext_vals.eqf.is_some()),
        (
            "TimeInvestmentExtension/context.json",
            ext_vals.time_investment.is_some(),
        ),
        (
            "SupervisionTypeExtension/context.json",
            ext_vals.supervision_type.is_some(),
        ),
        (
            "EducationProgramIdentifierExtension/context.json",
            ext_vals.education_program_identifier.is_some(),
        ),
    ];

    let urls: Vec<String> = ext_map
        .into_iter()
        .filter_map(|(filename, present)| {
            if present {
                Some(format!(
                    "{issuer_base_url}{extensions_url_prefix}/{filename}"
                ))
            } else {
                None
            }
        })
        .collect();

    if urls.is_empty() {
        None
    } else {
        Some(urls.into_iter().map(CredentialContextItem::Url).collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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

    // ─── TestDecodeFullResponse ────────────────────────────────────────────────

    #[test]
    fn test_decode_full_response() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/3527",
            "name": "Teamwork Badge",
            "issued_on": "2010-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/21",
                "name": "Teamwork Badge",
                "issuer": {
                    "name_dutch": null,
                    "name_english": null,
                    "faculty": null,
                },
            },
        });

        let result = ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None);
        assert!(result.is_ok());
        let award = result.unwrap();
        assert_eq!(award.id, "https://DOMAIN/assertions/3527");
        assert_eq!(award.name, "Teamwork Badge");
    }

    #[test]
    fn test_decode_response_with_missing_fields() {
        let raw = serde_json::json!({});
        let result = ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None);
        assert!(result.is_err());
    }

    #[test]
    fn test_from_dict_unknown_fields_ignored() {
        let raw = serde_json::json!({"unknown_field": "ignored"});
        let result = ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None);
        assert!(result.is_err());
    }

    #[test]
    fn test_from_dict_badgeclass_with_issuer() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Test Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/1",
                    "name_dutch": "NL",
                    "name_english": "EN",
                    "faculty": {
                        "entity_id": "https://ror.org/123",
                        "name_dutch": "FAC_NL",
                        "name_english": "FAC_EN",
                        "institution": {
                            "name_dutch": "University Voorbeeld",
                            "identifier": "university-example.org",
                        },
                    },
                },
            },
        });
        let result = ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None);
        assert!(result.is_ok());
        let award = result.unwrap();
        assert_eq!(award.name, "Test Badge");
        assert_eq!(award.issuer.id, "https://DOMAIN/issuers/1");
        assert_eq!(award.issuer.name, "EN");
    }

    #[test]
    fn test_from_dict_badgeclass_without_issuer() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Test Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": null,
            },
        });
        let result = ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None);
        assert!(result.is_ok());
        let award = result.unwrap();
        assert_eq!(award.name, "Test Badge");
        assert_eq!(award.issuer.name, "Test Badge");
    }

    // ─── TestToOb3Award ────────────────────────────────────────────────────────

    #[test]
    fn test_full_response_with_mapper_fields() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            "name": null,
            "issued_on": "2021-04-20T16:20:30.521307+02:00",
            "given_name": "Jan",
            "family_name": "Jansen",
            "email": "jan@example.com",
            "badgeclass": {
                "name": "Edubadge account complete",
                "entity_id": "https://DOMAIN/badges/nwsL-dHyQpmvOOKBscsN_A",
                "description": "Complete your account to start earning badges",
                "criteria_text": "Register and verify your email address",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/issuer-entity-id-123",
                    "name_dutch": "SURF Edubadges",
                    "name_english": "SURF Edubadges",
                    "faculty": null,
                },
            },
        });

        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();

        assert_eq!(
            result.id,
            "https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ"
        );
        assert_eq!(result.name, "Edubadge account complete");
        assert_eq!(result.valid_from, "2021-04-20T16:20:30.521307+02:00");
        assert_eq!(
            result.issuer.id,
            "https://DOMAIN/issuers/issuer-entity-id-123"
        );
        assert_eq!(result.issuer.name, "SURF Edubadges");
        assert_eq!(result.issuer.r#type, vec!["Profile"]);

        let subject = &result.credential_subject;
        assert_eq!(
            subject.achievement.criteria.narrative,
            "Register and verify your email address"
        );
        assert_eq!(
            subject.achievement.description,
            "Complete your account to start earning badges"
        );

        assert_eq!(subject.identifier.len(), 2);
        assert_eq!(subject.identifier[0].identity_hash, "jan@example.com");
        assert_eq!(subject.identifier[0].identity_type, "emailAddress");
        assert_eq!(subject.identifier[1].identity_hash, "Jan Jansen");
        assert_eq!(subject.identifier[1].identity_type, "name");
    }

    #[test]
    fn test_raises_when_entity_id_missing() {
        let raw = serde_json::json!({"name": "Badge", "issued_on": "2024-01-01T00:00:00Z"});
        let result = ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None);
        assert!(result.is_err());
    }

    #[test]
    fn test_badge_name_fallback_to_badgeclass_name() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": null,
            "issued_on": "2010-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Fallback Badge Name",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": null,
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.name, "Fallback Badge Name");
    }

    #[test]
    fn test_no_badge_name_or_badgeclass() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": null,
            "issued_on": null,
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.name, "");
    }

    #[test]
    fn test_identifiers_populated_with_email_and_name() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": "Badge",
            "issued_on": "2024-01-01T00:00:00Z",
            "given_name": "Jan",
            "family_name": "Jansen",
            "email": "jan@example.com",
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        let identifier = &result.credential_subject.identifier;
        assert_eq!(identifier.len(), 2);
        assert_eq!(identifier[0].identity_hash, "jan@example.com");
        assert_eq!(identifier[0].identity_type, "emailAddress");
        assert!(!identifier[0].hashed);
        assert_eq!(identifier[1].identity_hash, "Jan Jansen");
        assert_eq!(identifier[1].identity_type, "name");
    }

    #[test]
    fn test_identifiers_only_email_when_no_name() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": "Badge",
            "issued_on": "2024-01-01T00:00:00Z",
            "email": "solo@example.com",
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.credential_subject.identifier.len(), 1);
        assert_eq!(
            result.credential_subject.identifier[0].identity_hash,
            "solo@example.com"
        );
    }

    #[test]
    fn test_identifiers_only_name_when_no_email() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": "Badge",
            "issued_on": "2024-01-01T00:00:00Z",
            "given_name": "M",
            "family_name": "L",
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.credential_subject.identifier.len(), 1);
        assert_eq!(
            result.credential_subject.identifier[0].identity_type,
            "name"
        );
    }

    #[test]
    fn test_empty_identifiers_when_no_recipient_data() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": "Badge",
            "issued_on": "2024-01-01T00:00:00Z",
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert!(result.credential_subject.identifier.is_empty());
    }

    #[test]
    fn test_name_parts_filtered_for_none() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "name": "Badge",
            "issued_on": "2024-01-01T00:00:00Z",
            "given_name": "Single",
            "family_name": null,
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.credential_subject.identifier.len(), 1);
        assert_eq!(
            result.credential_subject.identifier[0].identity_hash,
            "Single"
        );
    }

    // ─── TestCredentialContextUrls ────────────────────────────────────────────

    #[test]
    fn test_credential_context_urls_empty_when_no_extension_fields() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {"entity_id": "https://DOMAIN/issuers/1"},
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert!(result.credential_context.is_none());
    }

    #[test]
    fn test_single_field_produces_single_url() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {"entity_id": "https://DOMAIN/issuers/1"},
                "learning_outcome": "Can do X",
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        let ctx = result.credential_context.unwrap();
        assert_eq!(ctx.len(), 1);
        if let CredentialContextItem::Url(url) = &ctx[0] {
            assert!(url.contains("LearningOutcomeExtension"));
        } else {
            panic!("Expected URL");
        }
    }

    #[test]
    fn test_all_flat_fields_produce_urls() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {"entity_id": "https://DOMAIN/issuers/1"},
                "language": "nl",
                "ects": "5",
                "learning_outcome": "Can do X",
                "education_program_identifier": ["12345"],
                "participation": ["enrolment", "onsite"],
                "assessment_type": ["testing", "portfolio"],
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        let ctx = result.credential_context.unwrap();
        assert_eq!(ctx.len(), 3);
    }

    #[test]
    fn test_none_fields_excluded() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {"entity_id": "https://DOMAIN/issuers/1"},
                "ects": null,
                "participation": ["enrolment"],
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert!(result.credential_context.is_none());
    }

    #[test]
    fn test_url_order_matches_field_order() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {"entity_id": "https://DOMAIN/issuers/1"},
                "language": "nl",
                "participation": ["enrolment"],
                "assessment_type": ["formative"],
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert!(result.credential_context.is_none());
    }

    // ─── TestOb3AwardWithNewFields ────────────────────────────────────────────

    #[test]
    fn test_to_ob3_award_with_expires_at() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            "issued_on": "2021-04-20T16:20:30.521307+02:00",
            "expires_at": "2024-04-20T16:20:30.521307+02:00",
            "badgeclass": default_badgeclass(None, None, None, None, None, None),
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(
            result.valid_until,
            Some("2024-04-20T16:20:30.521307+02:00".to_string())
        );
    }

    #[test]
    fn test_to_ob3_award_without_expires_at() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": default_badgeclass(None, None, None, None, None, None),
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert!(result.valid_until.is_none());
    }

    #[test]
    fn test_to_ob3_award_with_flat_field_extensions() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "expires_at": "2025-01-01T00:00:00Z",
            "badgeclass": default_badgeclass(
                Some(vec!["enrolment".to_string(), "onsite".to_string()]),
                Some(vec!["summative".to_string(), "formative".to_string()]),
                Some("nl".to_string()),
                Some("5".to_string()),
                Some(42.0),
                None,
            ),
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.valid_until, Some("2025-01-01T00:00:00Z".to_string()));
        let ach = &result.credential_subject.achievement;
        assert_eq!(ach.in_language, Some("nl".to_string()));
        assert_eq!(ach.ects, Some("5".to_string()));
        assert_eq!(ach.assessment_type, Some("summative,formative".to_string()));
        assert_eq!(
            ach.form_of_participation,
            Some(vec!["enrolment".to_string(), "onsite".to_string()])
        );
    }

    #[test]
    fn test_to_ob3_award_time_investment_from_raw_json() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/1",
                "name": "Badge",
                "issuer": {
                    "id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                },
                "TimeInvestment": 25.5,
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();
        assert_eq!(result.credential_subject.achievement.time_investment, None);
    }

    #[test]
    fn test_to_ob3_award_issuer_type_from_flat_field() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": default_badgeclass(None, None, None, None, None, Some("Organization".to_string())),
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.issuer.r#type, vec!["Organization"]);
    }

    #[test]
    fn test_to_ob3_award_issuer_type_fallback() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": default_badgeclass(None, None, None, None, None, None),
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        assert_eq!(result.issuer.r#type, vec!["Profile"]);
    }

    #[test]
    fn test_to_ob3_award_assessment_fields_produce_context_urls() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": default_badgeclass(
                Some(vec!["online".to_string(), "onsite".to_string()]),
                Some(vec!["summative".to_string(), "formative".to_string()]),
                None,
                None,
                None,
                None,
            ),
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("http://localhost:8000"), None).unwrap();
        let ach = &result.credential_subject.achievement;
        assert_eq!(ach.assessment_type, Some("summative,formative".to_string()));
        assert_eq!(
            ach.form_of_participation,
            Some(vec!["online".to_string(), "onsite".to_string()])
        );
    }

    #[test]
    fn test_extensions_from_raw_json() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "expiresAt": "2025-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/1",
                "name": "Badge",
                "issuer": {
                    "id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                },
                "Language": "nl_NL",
                "EducationProgramIdentifier": ["56823"],
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();
        let ach = &result.credential_subject.achievement;
        assert_eq!(ach.in_language, None);
        assert_eq!(ach.education_program_identifier, None);
    }

    #[test]
    fn test_criteria_narrative_from_nested_criteria() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "id": "https://DOMAIN/badges/1",
                "name": "Badge",
                "issuer": {
                    "id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                },
                "criteria": {
                    "narrative": "Will appreciate the benefits of learning a foreign language.",
                },
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();
        let ach = &result.credential_subject.achievement;
        assert_eq!(
            ach.criteria.narrative,
            "Will appreciate the benefits of learning a foreign language."
        );
    }

    // ─── ParentOrg Tests ──────────────────────────────────────────────────────

    #[test]
    fn test_resolve_issuer_populates_parent_org_from_faculty_institution() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/eshcc",
                    "name_english": "Erasmus School of History",
                    "faculty": {
                        "entity_id": "https://ror.org/57197",
                        "institution": {
                            "name_english": "Erasmus University Rotterdam",
                            "country_code": "NL",
                            "identifier": "eur.nl",
                            "brin": "21PE",
                        },
                    },
                },
            },
        });

        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();

        assert_eq!(result.issuer.id, "https://DOMAIN/issuers/eshcc");
        assert_eq!(result.issuer.name, "Erasmus School of History");
        let parent = result
            .issuer
            .parent_org
            .as_ref()
            .expect("parent_org should be set");
        assert_eq!(parent.id, "https://ror.org/57197");
        assert_eq!(parent.name, "Erasmus University Rotterdam");
        assert!(parent.address.is_some());
        assert_eq!(
            parent.address.as_ref().unwrap().address_country_code,
            Some("NL".to_string())
        );
        assert_eq!(parent.other_identifier.len(), 2);
        assert_eq!(parent.other_identifier[0].identifier, "21PE");
        assert_eq!(parent.other_identifier[0].identifier_type, "ext:BRIN");
        assert_eq!(parent.other_identifier[1].identifier, "eur.nl");
        assert_eq!(parent.other_identifier[1].identifier_type, "ext:SCHAC");
    }

    #[test]
    fn test_resolve_issuer_preserves_issuer_type_from_flat_field() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                    "type": "Organization",
                    "faculty": null,
                },
            },
        });

        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();
        assert_eq!(result.issuer.r#type, vec!["Organization"]);
    }

    #[test]
    fn test_resolve_issuer_with_country_code_and_identifiers() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                    "faculty": {
                        "entity_id": "https://ror.org/12345",
                        "institution": {
                            "name_english": "Test University",
                            "country_code": "DE",
                            "identifier": "test.de",
                            "brin": "AB12",
                        },
                    },
                },
            },
        });

        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();
        let parent = result
            .issuer
            .parent_org
            .as_ref()
            .expect("parent_org should be set");
        assert!(parent.address.is_some());
        assert_eq!(
            parent.address.as_ref().unwrap().address_country_code,
            Some("DE".to_string())
        );
        assert_eq!(parent.other_identifier[0].identifier, "AB12");
        assert_eq!(parent.other_identifier[0].identifier_type, "ext:BRIN");
        assert_eq!(parent.other_identifier[1].identifier, "test.de");
        assert_eq!(parent.other_identifier[1].identifier_type, "ext:SCHAC");
    }

    #[test]
    fn test_resolve_issuer_with_only_schac_or_brin() {
        let raw_schac = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                    "faculty": {
                        "institution": {
                            "identifier": "schac.example.org",
                        },
                    },
                },
            },
        });
        let result_schac =
            ob3_award_from_badgr_api_response(&raw_schac, None, Some("https://DOMAIN"), None).unwrap();
        assert_eq!(
            result_schac
                .issuer
                .parent_org
                .as_ref()
                .unwrap()
                .other_identifier
                .len(),
            1
        );
        assert_eq!(
            result_schac
                .issuer
                .parent_org
                .as_ref()
                .unwrap()
                .other_identifier[0]
                .identifier_type,
            "ext:SCHAC"
        );

        let raw_brin = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/1",
            "issued_on": "2024-01-01T00:00:00Z",
            "badgeclass": {
                "name": "Badge",
                "entity_id": "https://DOMAIN/badges/1",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/1",
                    "name_english": "Issuer",
                    "faculty": {
                        "institution": {
                            "brin": "BR1N99",
                        },
                    },
                },
            },
        });
        let result_brin =
            ob3_award_from_badgr_api_response(&raw_brin, None, Some("https://DOMAIN"), None).unwrap();
        assert_eq!(
            result_brin
                .issuer
                .parent_org
                .as_ref()
                .unwrap()
                .other_identifier
                .len(),
            1
        );
        assert_eq!(
            result_brin
                .issuer
                .parent_org
                .as_ref()
                .unwrap()
                .other_identifier[0]
                .identifier_type,
            "ext:BRIN"
        );
    }

    #[test]
    fn test_to_ob3_award_with_parent_org() {
        let raw = serde_json::json!({
            "entity_id": "https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ",
            "issued_on": "2021-04-20T16:20:30.521307+02:00",
            "given_name": "Jan",
            "family_name": "Jansen",
            "email": "jan@example.com",
            "badgeclass": {
                "name": "Edubadge account complete",
                "entity_id": "https://DOMAIN/badges/nwsL-dHyQpmvOOKBscsN_A",
                "description": "Complete your account",
                "criteria_text": "Register and verify email",
                "issuer": {
                    "entity_id": "https://DOMAIN/issuers/eshcc",
                    "name_english": "Erasmus School of History",
                    "faculty": {
                        "entity_id": "https://ror.org/57197",
                        "institution": {
                            "name_english": "Erasmus University Rotterdam",
                            "country_code": "NL",
                            "identifier": "eur.nl",
                            "brin": "21PE",
                        },
                    },
                },
            },
        });
        let result =
            ob3_award_from_badgr_api_response(&raw, None, Some("https://DOMAIN"), None).unwrap();
        let parent = result
            .issuer
            .parent_org
            .as_ref()
            .expect("parent_org should be set");
        assert_eq!(parent.id, "https://ror.org/57197");
        assert_eq!(parent.name, "Erasmus University Rotterdam");
        assert!(parent.address.is_some());
        assert_eq!(
            parent.address.as_ref().unwrap().address_country_code,
            Some("NL".to_string())
        );
        assert_eq!(parent.other_identifier.len(), 2);
    }
}
