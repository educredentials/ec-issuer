#![allow(clippy::used_underscore_items, clippy::unused_self)]

/// EC Issuer library.
///
/// Hexagonal architecture: domain models + ports (traits) in the center,
/// adapters (HTTP, Postgres, etc.) at the edges.
pub mod access_control;
/// HTTP API and extension context server.
pub mod api;
pub mod awards;
pub mod config;
pub mod credential_configurations;
pub mod credential_converter;
pub mod helpers;
pub mod offers;
pub mod revocation;
