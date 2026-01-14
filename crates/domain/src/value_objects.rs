//! Value Objects - Immutable domain concepts
//! These represent domain concepts that are defined by their attributes rather than identity

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::errors::{DomainError, DomainResult};

/// Credential status enumeration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum CredentialStatus {
    Active,
    Revoked,
    Expired,
    Suspended,
}

impl CredentialStatus {
    pub fn is_active(&self) -> bool {
        matches!(self, CredentialStatus::Active)
    }

    pub fn is_revoked(&self) -> bool {
        matches!(self, CredentialStatus::Revoked)
    }

    pub fn is_expired(&self) -> bool {
        matches!(self, CredentialStatus::Expired)
    }
}

impl std::fmt::Display for CredentialStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CredentialStatus::Active => write!(f, "active"),
            CredentialStatus::Revoked => write!(f, "revoked"),
            CredentialStatus::Expired => write!(f, "expired"),
            CredentialStatus::Suspended => write!(f, "suspended"),
        }
    }
}

impl std::str::FromStr for CredentialStatus {
    type Err = DomainError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "active" => Ok(CredentialStatus::Active),
            "revoked" => Ok(CredentialStatus::Revoked),
            "expired" => Ok(CredentialStatus::Expired),
            "suspended" => Ok(CredentialStatus::Suspended),
            _ => Err(DomainError::InvalidCredentialStatus {
                status: s.to_string(),
            }),
        }
    }
}

/// Credential format enumeration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum CredentialFormat {
    /// Open Badges 3.0
    #[serde(rename = "ob3")]
    OpenBadges3,
    /// European Learner Model
    #[serde(rename = "elm")]
    EuropeanLearnerModel,
}

impl std::fmt::Display for CredentialFormat {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CredentialFormat::OpenBadges3 => write!(f, "ob3"),
            CredentialFormat::EuropeanLearnerModel => write!(f, "elm"),
        }
    }
}

impl std::str::FromStr for CredentialFormat {
    type Err = DomainError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "ob3" | "openbadges3" | "open_badges_3" => Ok(CredentialFormat::OpenBadges3),
            "elm" | "european_learner_model" => Ok(CredentialFormat::EuropeanLearnerModel),
            _ => Err(DomainError::invalid_format(s)),
        }
    }
}

/// Credential Subject - represents the recipient
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CredentialSubject {
    pub id: String,
    pub name: Option<String>,
    pub email: Option<String>,
    #[serde(flatten)]
    pub additional_properties: serde_json::Value,
}

impl CredentialSubject {
    pub fn new(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            name: None,
            email: None,
            additional_properties: serde_json::json!({}),
        }
    }

    pub fn with_name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    pub fn with_email(mut self, email: impl Into<String>) -> Self {
        self.email = Some(email.into());
        self
    }

    pub fn validate(&self) -> DomainResult<()> {
        if self.id.is_empty() {
            return Err(DomainError::validation(
                "credentialSubject.id",
                "Subject ID cannot be empty",
            ));
        }

        if let Some(email) = &self.email {
            if !email.contains('@') {
                return Err(DomainError::validation(
                    "credentialSubject.email",
                    "Invalid email format",
                ));
            }
        }

        Ok(())
    }
}

/// Achievement - what was achieved
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Achievement {
    pub id: String,
    pub name: String,
    pub description: String,
    #[serde(rename = "type")]
    pub achievement_type: Vec<String>,
    pub criteria: Option<String>,
    pub image: Option<String>,
    #[serde(flatten)]
    pub additional_properties: serde_json::Value,
}

impl Achievement {
    pub fn new(
        id: impl Into<String>,
        name: impl Into<String>,
        description: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            description: description.into(),
            achievement_type: vec!["Achievement".to_string()],
            criteria: None,
            image: None,
            additional_properties: serde_json::json!({}),
        }
    }

    pub fn with_criteria(mut self, criteria: impl Into<String>) -> Self {
        self.criteria = Some(criteria.into());
        self
    }

    pub fn with_image(mut self, image: impl Into<String>) -> Self {
        self.image = Some(image.into());
        self
    }

    pub fn validate(&self) -> DomainResult<()> {
        if self.id.is_empty() {
            return Err(DomainError::validation(
                "achievement.id",
                "ID cannot be empty",
            ));
        }
        if self.name.is_empty() {
            return Err(DomainError::validation(
                "achievement.name",
                "Name cannot be empty",
            ));
        }

        if self.description.is_empty() {
            return Err(DomainError::validation(
                "achievement.description",
                "Description cannot be empty",
            ));
        }

        Ok(())
    }
}

/// Issuer - who issued the credential
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Issuer {
    pub id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub issuer_type: Vec<String>,
    pub url: Option<String>,
    pub email: Option<String>,
    pub image: Option<String>,
    #[serde(flatten)]
    pub additional_properties: serde_json::Value,
}

impl Issuer {
    pub fn new(id: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            issuer_type: vec!["Profile".to_string()],
            url: None,
            email: None,
            image: None,
            additional_properties: serde_json::json!({}),
        }
    }

    pub fn with_url(mut self, url: impl Into<String>) -> Self {
        self.url = Some(url.into());
        self
    }

    pub fn with_email(mut self, email: impl Into<String>) -> Self {
        self.email = Some(email.into());
        self
    }

    pub fn validate(&self) -> DomainResult<()> {
        if self.id.is_empty() {
            return Err(DomainError::validation("issuer.id", "ID cannot be empty"));
        }

        if self.name.is_empty() {
            return Err(DomainError::validation(
                "issuer.name",
                "Name cannot be empty",
            ));
        }
        Ok(())
    }
}

/// Revocation information
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RevocationInfo {
    pub revoked_at: DateTime<Utc>,
    pub reason: Option<String>,
    pub revoked_by: Option<String>,
}

impl RevocationInfo {
    pub fn new(reason: Option<String>) -> Self {
        Self {
            revoked_at: Utc::now(),
            reason,
            revoked_by: None,
        }
    }

    pub fn with_revoked_by(mut self, revoked_by: impl Into<String>) -> Self {
        self.revoked_by = Some(revoked_by.into());
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_credential_status_parsing() {
        assert_eq!(
            "active".parse::<CredentialStatus>().unwrap(),
            CredentialStatus::Active
        );
        assert_eq!(
            "revoked".parse::<CredentialStatus>().unwrap(),
            CredentialStatus::Revoked
        );
        assert!("in
            valid"
            .parse::<CredentialStatus>()
            .is_err());
    }

    #[test]
    fn test_credential_format_parsing() {
        assert_eq!(
            "ob3".parse::<CredentialFormat>().unwrap(),
            CredentialFormat::OpenBadges3
        );
        assert_eq!(
            "elm".parse::<CredentialFormat>().unwrap(),
            CredentialFormat::EuropeanLearnerModel
        );
        assert!("in
            valid"
            .parse::<CredentialFormat>()
            .is_err());
    }

    #[test]
    fn test_credential_subject_validation() {
        let subject = CredentialSubject::new("did:example:123").with_email("user@example.com");
        rt!(subject.validate().is_ok());

        let invalid_subject = CredentialSubject::new("").with_email("invalid-email");
        rt!(invalid_subject.validate().is_err());
    }

    #[test]
    fn test_achievement_validation() {
        let achievement = Achievement::new(
            "https://example.com/achievements/1",
            "Test Achievement",
            "Test Description",
        );
        assert!(achievement.validate().is_ok());

        let invalid = Achievement::new("", "", "");
        assert!(invalid.validate().is_err());
    }
}
