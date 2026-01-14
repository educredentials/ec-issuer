//! Application Services - Use Case Implementations
//!
//! These implement the inbound ports (use cases) and orchestrate the domain logic
//! using the outbound ports (infrastructure interfaces).

use async_trait::async_trait;
use credential_domain::{CredentialBuilder, CredentialSubject, DomainResult};
use std::sync::Arc;

use crate::inbound::*;
use crate::outbound::*;

/// Service for issuing credentials
pub struct CredentialService {
    repository: Arc<dyn CredentialRepository>,
    signing_client: Arc<dyn SigningClient>,
    achievement_client: Arc<dyn AchievementClient>,
    issuer_client: Arc<dyn IssuerClient>,
    event_publisher: Arc<dyn EventPublisher>,
    serializers: Vec<Arc<dyn CredentialSerializer>>,
}

impl CredentialService {
    pub fn new(
        repository: Arc<dyn CredentialRepository>,
        signing_client: Arc<dyn SigningClient>,
        achievement_client: Arc<dyn AchievementClient>,
        issuer_client: Arc<dyn IssuerClient>,
        event_publisher: Arc<dyn EventPublisher>,
        serializers: Vec<Arc<dyn CredentialSerializer>>,
    ) -> Self {
        Self {
            repository,
            signing_client,
            achievement_client,
            issuer_client,
            event_publisher,
            serializers,
        }
    }

    /// Find a serializer for the given format
    fn find_serializer(
        &self,
        format: credential_domain::CredentialFormat,
    ) -> Option<&Arc<dyn CredentialSerializer>> {
        self.serializers.iter().find(|s| s.format() == format)
    }
}

#[async_trait]
impl IssueCredentialUseCase for CredentialService {
    async fn execute(
        &self,
        request: IssueCredentialRequest,
    ) -> DomainResult<IssueCredentialResponse> {
        // Fetch achievement from external service
        let achievement = self
            .achievement_client
            .get_achievement(&request.achievement_id)
            .await?;

        // Fetch issuer from external service
        let issuer = self.issuer_client.get_issuer(&request.issuer_id).await?;

        // Build credential subject
        let mut subject = CredentialSubject::new(request.subject_id);
        if let Some(name) = request.subject_name {
            subject = subject.with_name(name);
        }
        if let Some(email) = request.subject_email {
            subject = subject.with_email(email);
        }

        // Build credential using domain logic
        let mut builder = CredentialBuilder::new()
            .credential_subject(subject)
            .achievement(achievement)
            .issuer(issuer);

        if let Some(expires_at) = request.expires_at {
            builder = builder.expires_at(expires_at);
        }

        if let Some(metadata) = request.metadata {
            builder = builder.metadata(metadata);
        }

        let mut credential = builder.build()?;

        // Sign the credential
        let proof = self.signing_client.sign(&credential).await?;
        credential.attach_proof(proof);

        // Persist the credential
        self.repository.save(&credential).await?;

        // Publish event
        self.event_publisher
            .publish_credential_issued(&credential)
            .await?;

        Ok(IssueCredentialResponse { credential })
    }
}

#[async_trait]
impl GetCredentialUseCase for CredentialService {
    async fn execute(&self, request: GetCredentialRequest) -> DomainResult<GetCredentialResponse> {
        // Fetch credential from repository
        let mut credential = self
            .repository
            .find_by_id(request.id)
            .await?
            .ok_or_else(|| credential_domain::DomainError::credential_not_found(request.id))?;

        // Update status if expired
        credential.update_status_if_expired();
        if credential.status != credential_domain::CredentialStatus::Active
            && !credential.is_expired()
        {
            self.repository.update(&credential).await?;
        }

        // Serialize to requested format if specified
        let formatted = if let Some(format) = request.format {
            let serializer = self.find_serializer(format).ok_or_else(|| {
                credential_domain::DomainError::invalid_format(format.to_string())
            })?;
            Some(serializer.serialize(&credential)?)
        } else {
            None
        };

        Ok(GetCredentialResponse {
            credential,
            formatted,
        })
    }
}

#[async_trait]
impl ListCredentialsUseCase for CredentialService {
    async fn execute(
        &self,
        request: ListCredentialsRequest,
    ) -> DomainResult<ListCredentialsResponse> {
        let filters = ListFilters {
            subject_id: request.subject_id,
            issuer_id: request.issuer_id,
            achievement_id: request.achievement_id,
            status: request.status,
            limit: request.limit,
            offset: request.offset,
        };

        let (credentials, total) = self.repository.list(filters).await?;

        Ok(ListCredentialsResponse { credentials, total })
    }
}

#[async_trait]
impl RevokeCredentialUseCase for CredentialService {
    async fn execute(
        &self,
        request: RevokeCredentialRequest,
    ) -> DomainResult<RevokeCredentialResponse> {
        // Fetch credential
        let mut credential = self
            .repository
            .find_by_id(request.id)
            .await?
            .ok_or_else(|| credential_domain::DomainError::credential_not_found(request.id))?;

        // Revoke using domain logic
        credential.revoke(request.reason)?;

        // Update in repository
        self.repository.update(&credential).await?;

        // Publish event
        self.event_publisher
            .publish_credential_revoked(&credential)
            .await?;

        Ok(RevokeCredentialResponse { credential })
    }
}

#[cfg(test)]
mod tests {

    // Mock implementations would go here for testing
    // This requires the mockall crate features to be properly configured
}
