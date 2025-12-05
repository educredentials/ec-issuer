//! Adapters Layer - Infrastructure Implementations
//!
//! This layer implements the ports (interfaces) defined by the domain.
//! It contains:
//! - HTTP API (Axum controllers)
//! - PostgreSQL repository (SQLx)
//! - gRPC signing client (Tonic)
//! - Stub implementations for external clients

pub mod http;
pub mod repository;
pub mod signing;
pub mod clients;
pub mod events;

// Re-export commonly used items
pub use repository::PostgresCredentialRepository;
pub use signing::{GrpcSigningClient, InMemorySigningClient};
pub use clients::{InMemoryAchievementClient, InMemoryIssuerClient, HttpAchievementClient, HttpIssuerClient};
pub use events::StubEventPublisher;
pub use http::{create_router, AppState};
