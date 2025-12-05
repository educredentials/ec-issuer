//! Domain Layer - Pure Business Logic
//!
//! This layer contains:
//! - Domain entities (Credential, Achievement, Issuer, etc.)
//! - Domain errors
//! - Business rules and validation logic
//!
//! IMPORTANT: This layer has ZERO dependencies on infrastructure.
//! No database, no HTTP, no external services.

pub mod entities;
pub mod errors;
pub mod value_objects;

pub use entities::*;
pub use errors::*;
pub use value_objects::*;
