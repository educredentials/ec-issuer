/// Ports (traits) for the offers module.
use crate::awards::models::OB3Award;

use super::models::{Offer, OfferCreated};

/// Error raised when API service returns 404.
#[derive(Debug, thiserror::Error)]
#[error("Offer not found: {0}")]
pub struct OfferNotFound(pub String);

/// Error raised when API service returns a non-404 error.
#[derive(Debug, thiserror::Error)]
#[error("Offers client error: {0}")]
pub struct OffersClientError(pub String);

impl From<crate::helpers::http_client::HttpClientError> for OffersClientError {
    fn from(e: crate::helpers::http_client::HttpClientError) -> Self {
        match e {
            crate::helpers::http_client::HttpClientError::Http { status, body } => {
                Self(format!("HTTP {status}: {body}"))
            }
            crate::helpers::http_client::HttpClientError::Connection(msg)
            | crate::helpers::http_client::HttpClientError::Serialization(msg) => Self(msg),
            crate::helpers::http_client::HttpClientError::Timeout => Self("Timeout".to_string()),
        }
    }
}

/// Port: repository interface for persisting and retrieving offers.
#[allow(async_fn_in_trait)]
pub trait OffersRepositoryPort {
    /// Persist an offer.
    ///
    /// # Arguments
    ///
    /// * `offer` - The offer to store.
    async fn store(&self, offer: Offer) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;

    /// Retrieve an offer by its identifier.
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The unique offer identifier.
    ///
    /// # Returns
    ///
    /// The matching Offer.
    async fn get(&self, offer_id: &str) -> Result<Offer, OfferNotFound>;

    /// Close any resources held by this repository.
    fn close(&self);

    /// Return true when the database is reachable.
    async fn health_check(&self) -> bool;
}

/// Port: interface for interacting with the SSI agent offers API.
pub trait OffersClientPort {
    /// Create an OB3 credential offer on the SSI agent.
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The offer identifier to create.
    /// * `award` - The OB3 `AchievementCredential` to issue.
    ///
    /// # Errors
    ///
    /// Returns `OffersClientError` on failure.
    fn create_ob3(
        &self,
        offer_id: &str,
        award: &OB3Award,
    ) -> Result<OfferCreated, OffersClientError>;

    /// Create an EDC credential offer on the SSI agent.
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The offer identifier to create.
    /// * `credential` - The ELM/EDC credential as a map.
    ///
    /// # Errors
    ///
    /// Returns `OffersClientError` on failure.
    fn create_edc(
        &self,
        offer_id: &str,
        credential: &serde_json::Value,
    ) -> Result<OfferCreated, OffersClientError>;

    /// Retrieve an offer by its identifier.
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The unique offer identifier.
    ///
    /// # Errors
    ///
    /// Returns `OffersClientError` on failure.
    fn get(&self, offer_id: &str) -> Result<Offer, OffersClientError>;

    /// Rollback a partially created offer (delete credential + offer).
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The offer identifier to roll back.
    ///
    /// # Errors
    ///
    /// Returns `OffersClientError` on failure.
    fn rollback(&self, offer_id: &str) -> Result<(), OffersClientError>;
}
