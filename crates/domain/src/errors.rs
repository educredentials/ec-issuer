//! Domain-level errors
//! These represent business rule violations and domain-specific error conditions

use thiserror::Error;
use uuid::Uuid;

#[derive(Error, Debug, Clone, PartialEq)]
pub enum DomainError {
    #[error("Validation error: {field}: {message}")]
    ValidationError { field: String, message: String },

    #[error("Credential not found: {id}")]
    CredentialNotFound { id: Uuid },

    #[error("Credential already revoked: {id}")]
    CredentialAlreadyRevoked { id: Uuid },

    #[error("Credential expired: {id}")]
    CredentialExpired { id: Uuid },

    #[error("Invalid credential status: {status}")]
    InvalidCredentialStatus { status: String },

    #[error("Achievement not found: {id}")]
    AchievementNotFound { id: String },

    #[error("Issuer not found: {id}")]
    IssuerNotFound { id: String },

    #[error("Invalid format: {format}")]
    InvalidFormat { format: String },

    #[error("Signing failed: {reason}")]
    SigningFailed { reason: String },

    #[error("Serialization error: {message}")]
    SerializationError { message: String },
}

impl DomainError {
    pub fn validation(field: impl Into<String>, message: impl Into<String>) -> Self {
        DomainError::ValidationError {
            field: field.into(),
            message: message.into(),
        }
    }

    pub fn credential_not_found(id: Uuid) -> Self {
        DomainError::CredentialNotFound { id }
    }

    pub fn credential_already_revoked(id: Uuid) -> Self {
        DomainError::CredentialAlreadyRevoked { id }
    }

    pub fn credential_expired(id: Uuid) -> Self {
        DomainError::CredentialExpired { id }
    }

    pub fn achievement_not_found(id: impl Into<String>) -> Self {
        DomainError::AchievementNotFound { id: id.into() }
    }

    pub fn issuer_not_found(id: impl Into<String>) -> Self {
        DomainError::IssuerNotFound { id: id.into() }
    }

    pub fn invalid_format(format: impl Into<String>) -> Self {
        DomainError::InvalidFormat {
            format: format.into(),
        }
    }

    pub fn signing_failed(reason: impl Into<String>) -> Self {
        DomainError::SigningFailed {
            reason: reason.into(),
        }
    }

    pub fn serialization_error(message: impl Into<String>) -> Self {
        DomainError::SerializationError {
            message: message.into(),
        }
    }
}

pub type DomainResult<T> = Result<T, DomainError>;
