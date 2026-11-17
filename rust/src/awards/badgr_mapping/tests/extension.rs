use crate::awards::badgr_dtos::BadgrAwardResponse;
use crate::awards::badgr_mapping::{
    _resolve_image, default_badgeclass, ob3_award_from_badgr_api_response,
};

use crate::awards::models::CredentialContextItem;

// ─── TestCredentialContextUrls ──────────────────────────────────────────────

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

// ─── TestOb3AwardWithNewFields ──────────────────────────────────────────────

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

// ─── ParentOrg Tests ────────────────────────────────────────────────────────

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

// ─── _resolve_image tests ───────────────────────────────────────────────────

#[test]
fn test_resolve_image_no_badgeclass() {
    let raw = serde_json::json!({"entity_id": "1", "issued_on": "2024-01-01T00:00:00Z"});
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, None);
    assert!(result.is_none());
}

#[test]
fn test_resolve_image_no_image_field() {
    let raw = serde_json::json!({
        "entity_id": "1", "issued_on": "2024-01-01T00:00:00Z",
        "badgeclass": {"name": "Test"}
    });
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, None);
    assert!(result.is_none());
}

#[test]
fn test_resolve_image_http_url() {
    let raw = serde_json::json!({
        "entity_id": "1", "issued_on": "2024-01-01T00:00:00Z",
        "badgeclass": {"name": "Test", "image": "http://example.com/img.png"}
    });
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, None);
    assert!(result.is_some());
    let map = result.unwrap();
    assert_eq!(
        map.get("id"),
        Some(&"http://example.com/img.png".to_string())
    );
    assert_eq!(map.get("type"), Some(&"Image".to_string()));
}

#[test]
fn test_resolve_image_https_url() {
    let raw = serde_json::json!({
        "entity_id": "1", "issued_on": "2024-01-01T00:00:00Z",
        "badgeclass": {"name": "Test", "image": "https://example.com/img.png"}
    });
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, None);
    assert!(result.is_some());
    let map = result.unwrap();
    assert_eq!(
        map.get("id"),
        Some(&"https://example.com/img.png".to_string())
    );
}

#[test]
fn test_resolve_image_relative_no_base() {
    let raw = serde_json::json!({
        "entity_id": "1", "issued_on": "2024-01-01T00:00:00Z",
        "badgeclass": {"name": "Test", "image": "/uploads/badge.png"}
    });
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, None);
    assert!(result.is_some());
    let map = result.unwrap();
    assert_eq!(map.get("id"), Some(&"/uploads/badge.png".to_string()));
}

#[test]
fn test_resolve_image_relative_with_base() {
    let raw = serde_json::json!({
        "entity_id": "1", "issued_on": "2024-01-01T00:00:00Z",
        "badgeclass": {"name": "Test", "image": "/uploads/badge.png"}
    });
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, Some("http://localhost:8000"));
    assert!(result.is_some());
    let map = result.unwrap();
    assert_eq!(
        map.get("id"),
        Some(&"http://localhost:8000/uploads/badge.png".to_string())
    );
}

#[test]
fn test_resolve_image_http_url_stays_absolute() {
    let raw = serde_json::json!({
        "entity_id": "1", "issued_on": "2024-01-01T00:00:00Z",
        "badgeclass": {"name": "Test", "image": "http://example.com/img.png"}
    });
    let dto = BadgrAwardResponse::from_json(&raw).unwrap();
    let result = _resolve_image(&dto, Some("http://localhost:8000"));
    assert!(result.is_some());
    let map = result.unwrap();
    assert_eq!(
        map.get("id"),
        Some(&"http://example.com/img.png".to_string())
    );
}
