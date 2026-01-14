//! HTTP API Adapter (Axum)
//!
//! REST API for credential operations

pub mod errors;
pub mod handlers;
pub mod routes;

pub use errors::*;
pub use handlers::*;
pub use routes::*;
