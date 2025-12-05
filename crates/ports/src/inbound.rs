//! Inbound Ports - Use Cases
//!
//! These traits define the application's use cases (business operations).
//! They are implemented by application services and called by adapters (e.g., HTTP controllers).

use async_trait::async_trait;
use credential_domain::{Credential, CredentialFormat, DomainResult};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Request to issue a new credential
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IssueCredentialRequest {
    pub subject_id: String,
    pub subject_name: Option<String>,
    pub subject_email: Option<String>,
    pub achievement_id: String,
    pub issuer_id: String,
    pub expires_at: Option<chrono::DateTime<chrono::Utc>>,
    pub metadata: Option<serde_json::Value>,
}

/// Response after issuing a credential
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IssueCredentialResponse {
    pub credential: Credential,
}

/// Request to get a credential in a specific format
#[derive(Debug, Clone)]
pub struct GetCredentialRequest {
    pub id: Uuid,
    pub format: Option<CredentialFormat>,
}

/// Response containing a formatted credential
#[derive(Debug, Clone)]
pub struct GetCredentialResponse {
    pub credential: Credential,
    pub formatted: Option<serde_json::Value>,
}

/// Request to list credentials with filters
#[derive(Debug, Clone, Default)]
pub struct ListCredentialsRequest {
    pub subject_id: Option<String>,
    pub issuer_id: Option<String>,
    pub achievement_id: Option<String>,
    pub status: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

/// Response containing a list of credentials
#[derive(Debug, Clone)]
pub struct ListCredentialsResponse {
    pub credentials: Vec<Credential>,
    pub total: i64,
}

/// Request to revoke a credential
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevokeCredentialRequest {
    pub id: Uuid,
    pub reason: Option<String>,
}

/// Response after revoking a credential
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevokeCredentialResponse {
    pub credential: Credential,
}

/// Use case: Issue a new credential
#[async_trait]
pub trait IssueCredentialUseCase: Send + Sync {
    async fn execute(&self, request: IssueCredentialRequest) -> DomainResult<IssueCredentialResponse>;
}

/// Use case: Get a credential by ID (optionally in a specific format)
#[async_trait]
pub trait GetCredentialUseCase: Send + Sync {
    async fn execute(&self, request: GetCredentialRequest) -> DomainResult<GetCredentialResponse>;
}

/// Use case: List credentials with filters
#[async_trait]
pub trait ListCredentialsUseCase: Send + Sync {
    async fn execute(&self, request: ListCredentialsRequest) -> DomainResult<ListCredentialsResponse>;
}

/// Use case: Revoke a credential
#[async_trait]
pub trait RevokeCredentialUseCase: Send + Sync {
    async fn execute(&self, request: RevokeCredentialRequest) -> DomainResult<RevokeCredentialResponse>;
}
