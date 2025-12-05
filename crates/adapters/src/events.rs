//! Event Publisher Adapters
//!
//! Implements the EventPublisher port for publishing domain events

use async_trait::async_trait;
use credential_domain::{Credential, DomainResult};
use credential_ports::EventPublisher;

/// Stub event publisher (logs events)
pub struct StubEventPublisher;

impl StubEventPublisher {
    pub fn new() -> Self {
        Self
    }
}

impl Default for StubEventPublisher {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl EventPublisher for StubEventPublisher {
    async fn publish_credential_issued(&self, credential: &Credential) -> DomainResult<()> {
        tracing::info!(
            credential_id = %credential.id,
            subject_id = %credential.credential_subject.id,
            "Credential issued event"
        );
        Ok(())
    }

    async fn publish_credential_revoked(&self, credential: &Credential) -> DomainResult<()> {
        tracing::info!(
            credential_id = %credential.id,
            "Credential revoked event"
        );
        Ok(())
    }
}

// In production, you might implement:
// - KafkaEventPublisher
// - RabbitMQEventPublisher
// - SNSEventPublisher
// etc.
