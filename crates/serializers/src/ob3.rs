//! Open Badges 3.0 Serializer
//!
//! Converts credentials to Open Badges 3.0 format with JSON-LD context

use credential_domain::{Credential, CredentialFormat, DomainError, DomainResult};
use credential_ports::CredentialSerializer;
use serde_json::{json, Value};

/// Serializer for Open Badges 3.0 format
pub struct OB3Serializer;

impl OB3Serializer {
    pub fn new() -> Self {
        Self
    }

    /// Convert credential to OB3 format
    fn to_ob3(&self, credential: &Credential) -> DomainResult<Value> {
        // Build the achievement object
        let achievement = json!({
            "id": credential.achievement.id,
            "type": credential.achievement.achievement_type,
            "name": credential.achievement.name,
            "description": credential.achievement.description,
            "criteria": credential.achievement.criteria.as_ref().map(|c| json!({
                "narrative": c
            })),
            "image": credential.achievement.image,
        });

        // Build the issuer object
        let issuer = json!({
            "id": credential.issuer.id,
            "type": credential.issuer.issuer_type,
            "name": credential.issuer.name,
            "url": credential.issuer.url,
            "email": credential.issuer.email,
            "image": credential.issuer.image,
        });

        // Build the credential subject
        let credential_subject = json!({
            "id": credential.credential_subject.id,
            "type": ["AchievementSubject"],
            "achievement": achievement,
        });

        // Build the main credential object
        let mut ob3_credential = json!({
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://purl.imsglobal.org/spec/ob/v3p0/context.json"
            ],
            "id": format!("urn:uuid:{}", credential.id),
            "type": ["VerifiableCredential", "OpenBadgeCredential"],
            "issuer": issuer,
            "issuanceDate": credential.issued_at.to_rfc3339(),
            "credentialSubject": credential_subject,
        });

        // Add expiration date if present
        if let Some(expires_at) = credential.expires_at {
            ob3_credential["expirationDate"] = json!(expires_at.to_rfc3339());
        }

        // Add proof if present
        if let Some(ref proof) = credential.proof {
            ob3_credential["proof"] = proof.clone();
        }

        // Add credential status if revoked
        if credential.status.is_revoked() {
            if let Some(ref revocation_info) = credential.revocation_info {
                ob3_credential["credentialStatus"] = json!({
                    "id": format!("urn:uuid:{}#status", credential.id),
                    "type": "StatusList2021Entry",
                    "statusPurpose": "revocation",
                    "statusListIndex": "0",
                    "statusListCredential": format!("https://example.com/status/{}", credential.id),
                    "revocationReason": revocation_info.reason,
                    "revokedAt": revocation_info.revoked_at.to_rfc3339(),
                });
            }
        }

        Ok(ob3_credential)
    }

    /// Parse OB3 format to canonical credential (basic implementation)
    fn from_ob3(_data: &Value) -> DomainResult<Credential> {
        // This would require full parsing logic - stub for now
        Err(DomainError::serialization_error(
            "Deserialization from OB3 not yet implemented",
        ))
    }
}

impl Default for OB3Serializer {
    fn default() -> Self {
        Self::new()
    }
}

impl CredentialSerializer for OB3Serializer {
    fn format(&self) -> CredentialFormat {
        CredentialFormat::OpenBadges3
    }

    fn serialize(&self, credential: &Credential) -> DomainResult<Value> {
        self.to_ob3(credential)
    }

    fn deserialize(&self, data: &Value) -> DomainResult<Credential> {
        OB3Serializer::from_ob3(data)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use credential_domain::{Achievement, CredentialSubject, Issuer};

    fn create_test_credential() -> Credential {
        let subject = CredentialSubject::new("did:example:recipient")
            .with_name("Test User")
            .with_email("test@example.com");

        let achievement = Achievement::new(
            "https://example.com/achievements/1",
            "Test Achievement",
            "A test achievement",
        );

        let issuer = Issuer::new("https://example.com/issuer", "Test Issuer")
            .with_url("https://example.com");

        Credential::new(subject, achievement, issuer).unwrap()
    }

    #[test]
    fn test_ob3_serialization() {
        let credential = create_test_credential();
        let serializer = OB3Serializer::new();

        let ob3 = serializer.serialize(&credential).unwrap();

        // Verify JSON-LD context
        assert!(ob3["@context"].is_array());
        assert_eq!(ob3["@context"][0], "https://www.w3.org/2018/credentials/v1");

        // Verify types
        assert!(ob3["type"]
            .as_array()
            .unwrap()
            .contains(&json!("OpenBadgeCredential")));

        // Verify structure
        assert!(ob3["issuer"].is_object());
        assert!(ob3["credentialSubject"].is_object());
        assert!(ob3["issuanceDate"].is_string());
    }

    #[test]
    fn test_ob3_with_expiration() {
        let credential = create_test_credential();
        let future = chrono::Utc::now() + chrono::Duration::days(30);
        let credential = credential.with_expiration(future).unwrap();

        let serializer = OB3Serializer::new();
        let ob3 = serializer.serialize(&credential).unwrap();

        assert!(ob3["expirationDate"].is_string());
    }

    #[test]
    fn test_ob3_format() {
        let serializer = OB3Serializer::new();
        assert_eq!(serializer.format(), CredentialFormat::OpenBadges3);
    }
}
