//! European Learner Model (ELM) Serializer
//!
//! Converts credentials to ELM format

use credential_domain::{Credential, CredentialFormat, DomainError, DomainResult};
use credential_ports::CredentialSerializer;
use serde_json::{json, Value};

/// Serializer for European Learner Model format
pub struct ELMSerializer;

impl ELMSerializer {
    pub fn new() -> Self {
        Self
    }

    /// Convert credential to ELM format
    fn to_elm(&self, credential: &Credential) -> DomainResult<Value> {
        // Build the learning achievement
        let learning_achievement = json!({
            "id": credential.achievement.id,
            "title": credential.achievement.name,
            "description": credential.achievement.description,
            "additionalNote": credential.achievement.criteria,
        });

        // Build the awarding body (issuer)
        let awarding_body = json!({
            "id": credential.issuer.id,
            "preferredName": credential.issuer.name,
            "homepage": credential.issuer.url,
            "contactPoint": credential.issuer.email.as_ref().map(|e| json!({
                "email": e
            })),
        });

        // Build the learner (subject)
        let learner = json!({
            "id": credential.credential_subject.id,
            "fullName": credential.credential_subject.name,
            "contactPoint": credential.credential_subject.email.as_ref().map(|e| json!({
                "email": e
            })),
        });

        // Build the main ELM credential
        let mut elm_credential = json!({
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://europa.eu/europass/model/credentials/v1"
            ],
            "id": format!("urn:credential:{}", credential.id),
            "type": ["VerifiableCredential", "EuropassCredential"],
            "issuer": awarding_body,
            "issuanceDate": credential.issued_at.to_rfc3339(),
            "credentialSubject": {
                "id": learner["id"],
                "type": ["Person"],
                "fullName": learner["fullName"],
                "achieved": [{
                    "id": learning_achievement["id"],
                    "title": learning_achievement["title"],
                    "description": learning_achievement["description"],
                    "learningAchievement": learning_achievement,
                    "awardedBy": awarding_body,
                }]
            },
        });

        // Add expiration date if present
        if let Some(expires_at) = credential.expires_at {
            elm_credential["expirationDate"] = json!(expires_at.to_rfc3339());
        }

        // Add proof if present
        if let Some(ref proof) = credential.proof {
            elm_credential["proof"] = proof.clone();
        }

        // Add credential status if revoked
        if credential.status.is_revoked() {
            if let Some(ref revocation_info) = credential.revocation_info {
                elm_credential["credentialStatus"] = json!({
                    "id": format!("urn:credential:{}#status", credential.id),
                    "type": "CredentialStatusList2021",
                    "statusPurpose": "revocation",
                    "statusReason": revocation_info.reason,
                    "statusDate": revocation_info.revoked_at.to_rfc3339(),
                });
            }
        }

        Ok(elm_credential)
    }

    /// Parse ELM format to canonical credential (basic implementation)
    fn from_elm(_data: &Value) -> DomainResult<Credential> {
        // This would require full parsing logic - stub for now
        Err(DomainError::serialization_error(
            "Deserialization from ELM not yet implemented",
        ))
    }
}

impl Default for ELMSerializer {
    fn default() -> Self {
        Self::new()
    }
}

impl CredentialSerializer for ELMSerializer {
    fn format(&self) -> CredentialFormat {
        CredentialFormat::EuropeanLearnerModel
    }

    fn serialize(&self, credential: &Credential) -> DomainResult<Value> {
        self.to_elm(credential)
    }

    fn deserialize(&self, data: &Value) -> DomainResult<Credential> {
        ELMSerializer::from_elm(data)
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
    fn test_elm_serialization() {
        let credential = create_test_credential();
        let serializer = ELMSerializer::new();

        let elm = serializer.serialize(&credential).unwrap();

        // Verify JSON-LD context
        assert!(elm["@context"].is_array());

        // Verify types
        assert!(elm["type"]
            .as_array()
            .unwrap()
            .contains(&json!("EuropassCredential")));

        // Verify structure
        assert!(elm["issuer"].is_object());
        assert!(elm["credentialSubject"].is_object());
        assert!(elm["issuanceDate"].is_string());
    }

    #[test]
    fn test_elm_format() {
        let serializer = ELMSerializer::new();
        assert_eq!(serializer.format(), CredentialFormat::EuropeanLearnerModel);
    }

    #[test]
    fn test_elm_with_achievement() {
        let credential = create_test_credential();
        let serializer = ELMSerializer::new();

        let elm = serializer.serialize(&credential).unwrap();

        let achieved = elm["credentialSubject"]["achieved"].as_array().unwrap();
        assert!(!achieved.is_empty());
        assert!(achieved[0]["learningAchievement"].is_object());
    }
}
