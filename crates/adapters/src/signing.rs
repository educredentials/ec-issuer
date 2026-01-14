//! gRPC Signing Client Adapter
//!
//! Implements the SigningClient port using Tonic gRPC

use async_trait::async_trait;
use credential_domain::{Credential, DomainResult};
use credential_ports::SigningClient;
use serde_json::json;

/// gRPC-based signing client
pub struct GrpcSigningClient {
    service_url: String,
}

impl GrpcSigningClient {
    pub fn new(service_url: String) -> Self {
        Self { service_url }
    }
}

#[async_trait]
impl SigningClient for GrpcSigningClient {
    async fn sign(&self, credential: &Credential) -> DomainResult<serde_json::Value> {
        // TODO: Implement actual gRPC call to signing service
        // This is a stub implementation that returns a mock proof

        tracing::info!(
            "Signing credential {} via gRPC at {}",
            credential.id,
            self.service_url
        );

        // Mock proof - in production, this would call the signing service
        let proof = json!({
            "type": "Ed25519Signature2020",
            "created": chrono::Utc::now().to_rfc3339(),
            "verificationMethod": format!("{}#key-1", credential.issuer.id),
            "proofPurpose": "assertionMethod",
            "proofValue": "mock-signature-value-would-be-here"
        });

        Ok(proof)
    }

    async fn verify(&self, credential: &Credential) -> DomainResult<bool> {
        // TODO: Implement actual gRPC call to signing service for verification

        tracing::info!(
            "Verifying credential {} via gRPC at {}",
            credential.id,
            self.service_url
        );

        // Mock verification - always returns true for now
        Ok(credential.proof.is_some())
    }
}

/// In-memory signing client for testing
pub struct InMemorySigningClient;

impl InMemorySigningClient {
    pub fn new() -> Self {
        Self
    }
}

impl Default for InMemorySigningClient {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl SigningClient for InMemorySigningClient {
    async fn sign(&self, credential: &Credential) -> DomainResult<serde_json::Value> {
        // Generate a mock proof for testing
        let proof = json!({
            "type": "Ed25519Signature2020",
            "created": chrono::Utc::now().to_rfc3339(),
            "verificationMethod": format!("{}#key-1", credential.issuer.id),
            "proofPurpose": "assertionMethod",
            "proofValue": format!("mock-signature-{}", credential.id)
        });

        Ok(proof)
    }

    async fn verify(&self, credential: &Credential) -> DomainResult<bool> {
        Ok(credential.proof.is_some())
    }
}

// Proto definitions would typically be generated via build.rs
// For now, we'll use the stub implementations above
