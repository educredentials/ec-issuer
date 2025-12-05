//! Outbound Ports - Infrastructure Interfaces
//!
//! These traits define interfaces to external systems and infrastructure.
//! They are implemented by adapters (e.g., PostgreSQL repository, gRPC client).

use async_trait::async_trait;
use credential_domain::{Achievement, Credential, CredentialFormat, DomainResult, Issuer};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Repository for persisting credentials
#[async_trait]
pub trait CredentialRepository: Send + Sync {
    /// Save a new credential
    async fn save(&self, credential: &Credential) -> DomainResult<()>;

    /// Find a credential by ID
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Credential>>;

    /// Update an existing credential
    async fn update(&self, credential: &Credential) -> DomainResult<()>;

    /// List credentials with filters
    async fn list(&self, filters: ListFilters) -> DomainResult<(Vec<Credential>, i64)>;

    /// Delete a credential (for testing purposes)
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}

/// Filters for listing credentials
#[derive(Debug, Clone, Default)]
pub struct ListFilters {
    pub subject_id: Option<String>,
    pub issuer_id: Option<String>,
    pub achievement_id: Option<String>,
    pub status: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

/// Client for signing credentials
#[async_trait]
pub trait SigningClient: Send + Sync {
    /// Sign a credential and return the proof
    async fn sign(&self, credential: &Credential) -> DomainResult<serde_json::Value>;

    /// Verify a signed credential
    async fn verify(&self, credential: &Credential) -> DomainResult<bool>;
}

/// Request to sign data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignRequest {
    pub data: serde_json::Value,
    pub key_id: String,
}

/// Response from signing service
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignResponse {
    pub proof: serde_json::Value,
}

/// Client for fetching achievement definitions
#[async_trait]
pub trait AchievementClient: Send + Sync {
    /// Fetch an achievement by ID
    async fn get_achievement(&self, id: &str) -> DomainResult<Achievement>;
}

/// Client for fetching issuer information
#[async_trait]
pub trait IssuerClient: Send + Sync {
    /// Fetch an issuer by ID
    async fn get_issuer(&self, id: &str) -> DomainResult<Issuer>;
}

/// Event publisher for domain events
#[async_trait]
pub trait EventPublisher: Send + Sync {
    /// Publish a credential issued event
    async fn publish_credential_issued(&self, credential: &Credential) -> DomainResult<()>;

    /// Publish a credential revoked event
    async fn publish_credential_revoked(&self, credential: &Credential) -> DomainResult<()>;
}

/// Event types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialIssuedEvent {
    pub credential_id: Uuid,
    pub subject_id: String,
    pub achievement_id: String,
    pub issuer_id: String,
    pub issued_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialRevokedEvent {
    pub credential_id: Uuid,
    pub revoked_at: chrono::DateTime<chrono::Utc>,
    pub reason: Option<String>,
}

/// Serializer for converting credentials to specific formats
pub trait CredentialSerializer: Send + Sync {
    /// Get the format this serializer handles
    fn format(&self) -> CredentialFormat;

    /// Serialize a credential to the specific format
    fn serialize(&self, credential: &Credential) -> DomainResult<serde_json::Value>;

    /// Deserialize from the specific format (if supported)
    fn deserialize(&self, data: &serde_json::Value) -> DomainResult<Credential>;
}
