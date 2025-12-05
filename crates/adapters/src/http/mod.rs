//! HTTP API Adapter (Axum)
//!
//! REST API for credential operations

pub mod handlers;
pub mod routes;
pub mod errors;

pub use handlers::*;
pub use routes::*;
pub use errors::*;
