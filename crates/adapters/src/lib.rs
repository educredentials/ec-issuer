//! Adapters Layer - Infrastructure Implementations
//!
//! This layer implements the ports (interfaces) defined by the domain.
//! It contains:
//! - HTTP API (Axum controllers)
//! - PostgreSQL repository (SQLx)
//! - gRPC signing client (Tonic)
//! - Stub implementations for external clients

pub mod clients;
pub mod events;
pub mod http;
pub mod repository;
pub mod signing;

// Re-export commonly used items
pub use clients::{
    HttpAchievementClient, HttpIssuerClient, InMemoryAchievementClient, InMemoryIssuerClient,
};
pub use events::StubEventPublisher;
pub use http::{create_router, AppState};
pub use repository::PostgresCredentialRepository;
pub use signing::{GrpcSigningClient, InMemorySigningClient};
