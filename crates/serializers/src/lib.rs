//! Serializers - Format-specific credential representations
//!
//! This layer converts the canonical domain model to specific formats:
//! - Open Badges 3.0 (OB3)
//! - European Learner Model (ELM)

pub mod ob3;
pub mod elm;

pub use ob3::OB3Serializer;
pub use elm::ELMSerializer;
