//! Ports Layer - Interface Definitions
//!
//! This layer defines the interfaces (traits) that the domain uses to interact
//! with the outside world. These are implemented by adapters.
//!
//! Hexagonal Architecture:
//! - Inbound ports: Use cases that drive the application (e.g., IssueCredentialUseCase)
//! - Outbound ports: Infrastructure interfaces (e.g., CredentialRepository, SigningClient)

pub mod inbound;
pub mod outbound;
pub mod services;

pub use inbound::*;
pub use outbound::*;
pub use services::*;
