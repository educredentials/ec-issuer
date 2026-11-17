use crate::awards::badgr_mapping::ob3_award_from_badgr_api_response;

// ─── TestDecodeFullResponse ─────────────────────────────────────────────────

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

// ─── TestToOb3Award ──────────────────────────────────────────────────────────

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
