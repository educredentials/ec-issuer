//! Domain Entities - Core business objects with identity
//! These are the heart of the domain model

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::errors::{DomainError, DomainResult};
use crate::value_objects::*;

/// Credential - the core domain entity
///
/// Represents a verifiable credential that can be issued to a subject.
/// This is the canonical representation used throughout the domain layer.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Credential {
    /// Unique identifier for this credential
    pub id: Uuid,

    /// The subject (recipient) of this credential
    pub credential_subject: CredentialSubject,

    /// The achievement being attested
    pub achievement: Achievement,

    /// The issuer of this credential
    pub issuer: Issuer,

    /// Current status of the credential
    pub status: CredentialStatus,

    /// When the credential was issued
    pub issued_at: DateTime<Utc>,

    /// Optional expiration date
    pub expires_at: Option<DateTime<Utc>>,

    /// Revocation information (if revoked)
    pub revocation_info: Option<RevocationInfo>,

    /// Digital signature (proof) - set after signing
    pub proof: Option<serde_json::Value>,

    /// Additional metadata
    pub metadata: serde_json::Value,

    /// When this record was created
    pub created_at: DateTime<Utc>,

    /// When this record was last updated
    pub updated_at: DateTime<Utc>,
}

impl Credential {
    /// Create a new credential (for issuance)
    pub fn new(
        credential_subject: CredentialSubject,
        achievement: Achievement,
        issuer: Issuer,
    ) -> DomainResult<Self> {
        let now = Utc::now();

        let credential = Self {
            id: Uuid::new_v4(),
            credential_subject,
            achievement,
            issuer,
            status: CredentialStatus::Active,
            issued_at: now,
            expires_at: None,
            revocation_info: None,
            proof: None,
            metadata: serde_json::json!({}),
            created_at: now,
            updated_at: now,
        };

        // Validate upon creation
        credential.validate()?;

        Ok(credential)
    }

    /// Set expiration date
    pub fn with_expiration(mut self, expires_at: DateTime<Utc>) -> DomainResult<Self> {
        if expires_at <= self.issued_at {
            return Err(DomainError::validation(
                "expires_at",
                "Expiration date must be after issuance date",
            ));
        }
        self.expires_at = Some(expires_at);
        Ok(self)
    }

    /// Set metadata
    pub fn with_metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = metadata;
        self
    }

    /// Attach proof/signature to the credential
    pub fn attach_proof(&mut self, proof: serde_json::Value) {
        self.proof = Some(proof);
        self.updated_at = Utc::now();
    }

    /// Revoke the credential
    pub fn revoke(&mut self, reason: Option<String>) -> DomainResult<()> {
        if self.status.is_revoked() {
            return Err(DomainError::credential_already_revoked(self.id));
        }

        self.status = CredentialStatus::Revoked;
        self.revocation_info = Some(RevocationInfo::new(reason));
        self.updated_at = Utc::now();

        Ok(())
    }

    /// Check if credential is expired
    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            Utc::now() > expires_at
        } else {
            false
        }
    }

    /// Update status based on expiration
    pub fn update_status_if_expired(&mut self) {
        if self.is_expired() && self.status == CredentialStatus::Active {
            self.status = CredentialStatus::Expired;
            self.updated_at = Utc::now();
        }
    }

    /// Check if credential is valid (active and not expired)
    pub fn is_valid(&self) -> bool {
        self.status.is_active() && !self.is_expired()
    }

    /// Validate all business rules
    pub fn validate(&self) -> DomainResult<()> {
        // Validate credential subject
        self.credential_subject.validate()?;

        // Validate achievement
        self.achievement.validate()?;

        // Validate issuer
        self.issuer.validate()?;

        // Validate expiration if set
        if let Some(expires_at) = self.expires_at {
            if expires_at <= self.issued_at {
                return Err(DomainError::validation(
                    "expires_at",
                    "Expiration date must be after issuance date",
                ));
            }
        }

        // Validate revocation info consistency
        if self.status.is_revoked() && self.revocation_info.is_none() {
            return Err(DomainError::validation(
                "revocation_info",
                "Revoked credentials must have revocation info",
            ));
        }

        if !self.status.is_revoked() && self.revocation_info.is_some() {
            return Err(DomainError::validation(
                "revocation_info",
                "Non-revoked credentials cannot have revocation info",
            ));
        }

        Ok(())
    }
}

/// Builder for creating credentials with a fluent interface
pub struct CredentialBuilder {
    credential_subject: Option<CredentialSubject>,
    achievement: Option<Achievement>,
    issuer: Option<Issuer>,
    expires_at: Option<DateTime<Utc>>,
    metadata: Option<serde_json::Value>,
}

impl CredentialBuilder {
    pub fn new() -> Self {
        Self {
            credential_subject: None,
            achievement: None,
            issuer: None,
            expires_at: None,
            metadata: None,
        }
    }

    pub fn credential_subject(mut self, subject: CredentialSubject) -> Self {
        self.credential_subject = Some(subject);
        self
    }

    pub fn achievement(mut self, achievement: Achievement) -> Self {
        self.achievement = Some(achievement);
        self
    }

    pub fn issuer(mut self, issuer: Issuer) -> Self {
        self.issuer = Some(issuer);
        self
    }

    pub fn expires_at(mut self, expires_at: DateTime<Utc>) -> Self {
        self.expires_at = Some(expires_at);
        self
    }

    pub fn metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = Some(metadata);
        self
    }

    pub fn build(self) -> DomainResult<Credential> {
        let subject = self.credential_subject.ok_or_else(|| {
            DomainError::validation("credential_subject", "Credential subject is required")
        })?;

        let achievement = self
            .achievement
            .ok_or_else(|| DomainError::validation("achievement", "Achievement is required"))?;

        let issuer = self
            .issuer
            .ok_or_else(|| DomainError::validation("issuer", "Issuer is required"))?;

        let mut credential = Credential::new(subject, achievement, issuer)?;

        if let Some(expires_at) = self.expires_at {
            credential = credential.with_expiration(expires_at)?;
        }

        if let Some(metadata) = self.metadata {
            credential = credential.with_metadata(metadata);
        }

        Ok(credential)
    }
}

impl Default for CredentialBuilder {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn test_credential_creation() {
        let credential = create_test_credential();
        assert_eq!(credential.status, CredentialStatus::Active);
        assert!(credential.is_valid());
        assert!(credential.proof.is_none());
    }

    #[test]
    fn test_credential_with_expiration() {
        let credential = create_test_credential();
        let future = Utc::now() + chrono::Duration::days(30);
        let credential = credential.with_expiration(future).unwrap();

        assert!(credential.expires_at.is_some());
        assert!(!credential.is_expired());
    }

    #[test]
    fn test_credential_revocation() {
        let mut credential = create_test_credential();

        assert!(credential.revoke(Some("Testing".to_string())).is_ok());
        assert_eq!(credential.status, CredentialStatus::Revoked);
        assert!(credential.revocation_info.is_some());
        assert!(!credential.is_valid());

        // Cannot revoke twice
        assert!(credential.revoke(None).is_err());
    }

    #[test]
    fn test_credential_expiration() {
        let subject = CredentialSubject::new("did:example:recipient");
        let achievement = Achievement::new("id", "name", "desc");
        let issuer = Issuer::new("issuer-id", "Issuer");

        let mut credential = Credential::new(subject, achievement, issuer).unwrap();

        // Set expiration in the past
        let past = Utc::now() - chrono::Duration::days(1);
        credential.expires_at = Some(past);

        assert!(credential.is_expired());
        credential.update_status_if_expired();
        assert_eq!(credential.status, CredentialStatus::Expired);
        assert!(!credential.is_valid());
    }

    #[test]
    fn test_credential_builder() {
        let subject = CredentialSubject::new("did:example:recipient");
        let achievement = Achievement::new("id", "name", "desc");
        let issuer = Issuer::new("issuer-id", "Issuer");

        let credential = CredentialBuilder::new()
            .credential_subject(subject)
            .achievement(achievement)
            .issuer(issuer)
            .metadata(serde_json::json!({"foo": "bar"}))
            .build()
            .unwrap();

        assert_eq!(credential.metadata["foo"], "bar");
    }

    #[test]
    fn test_attach_proof() {
        let mut credential = create_test_credential();
        let proof = serde_json::json!({
            "type": "Ed25519Signature2020",
            "proofValue": "abc123"
        });

        credential.attach_proof(proof.clone());
        assert_eq!(credential.proof, Some(proof));
    }
}
