/// PostgreSQL adapter for the offers repository.
use sqlx::{PgPool, Row};

use super::models::Offer;
use super::port::{OfferNotFound, OffersRepositoryPort};

/// PostgreSQL implementation of the offers repository.
pub struct OffersRepository {
    /// Database connection pool.
    pool: PgPool,
}

impl OffersRepository {
    /// Create a new offers repository backed by PostgreSQL.
    ///
    /// # Arguments
    ///
    /// * `pool` - PostgreSQL connection pool.
    #[must_use]
    pub const fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Initialise the database table for offers.
    ///
    /// # Errors
    ///
    /// Returns `sqlx::Error` on failure.
    pub async fn init_db(&self) -> Result<(), sqlx::Error> {
        sqlx::query(
            r"
            CREATE TABLE IF NOT EXISTS offers (
                offer_id TEXT PRIMARY KEY,
                award_id TEXT NOT NULL,
                credential_ids TEXT[] NULL,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
            ",
        )
        .execute(&self.pool)
        .await?;
        Ok(())
    }
}

impl OffersRepositoryPort for OffersRepository {
    /// Persist an offer in PostgreSQL.
    ///
    /// # Arguments
    ///
    /// * `offer` - The offer to store.
    ///
    /// # Errors
    ///
    /// Returns an error if the INSERT fails.
    async fn store(&self, offer: Offer) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let created_at = offer.created_at.unwrap_or_else(chrono::Utc::now);

        let credential_ids: Vec<String> = offer.credential_ids.clone();

        sqlx::query(
            r"
            INSERT INTO offers (offer_id, award_id, credential_ids, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (offer_id) DO UPDATE
            SET award_id = EXCLUDED.award_id,
                credential_ids = EXCLUDED.credential_ids,
                created_at = EXCLUDED.created_at
            ",
        )
        .bind(&offer.offer_id)
        .bind(&offer.award_id)
        .bind(credential_ids)
        .bind(created_at)
        .execute(&self.pool)
        .await
        .map_err(|e| e.to_string())?;

        Ok(())
    }

    /// Retrieve an offer by its identifier.
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The unique offer identifier.
    ///
    /// # Errors
    ///
    /// Returns `OfferNotFound` when no offer with the given id exists.
    async fn get(&self, offer_id: &str) -> Result<Offer, OfferNotFound> {
        let row = sqlx::query(
            r"
            SELECT offer_id, award_id, credential_ids, created_at
            FROM offers
            WHERE offer_id = $1
            ",
        )
        .bind(offer_id)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| OfferNotFound(e.to_string()))?;

        let row = row.ok_or_else(|| OfferNotFound(offer_id.to_string()))?;

        Ok(Offer {
            offer_id: row
                .try_get("offer_id")
                .map_err(|e| e.to_string())
                .map_err(OfferNotFound)?,
            award_id: row
                .try_get("award_id")
                .map_err(|e| e.to_string())
                .map_err(OfferNotFound)?,
            uri: None,
            credential_ids: row.try_get("credential_ids").unwrap_or_default(),
            created_at: row.try_get("created_at").ok(),
        })
    }

    /// Close any resources held by this repository.
    fn close(&self) {
        // PgPool is dropped when OffersRepository is dropped.
    }

    /// Return true when the database is reachable.
    async fn health_check(&self) -> bool {
        sqlx::query("SELECT 1")
            .fetch_optional(&self.pool)
            .await
            .is_ok()
    }
}

/// Test helper: create an offers repository backed by a real PostgreSQL
/// instance running on the given connection string.
///
/// # Errors
///
/// Returns the underlying `sqlx::Error` if connection or migration fails.
pub async fn create_test_repository(
    connection_string: &str,
) -> Result<OffersRepository, sqlx::Error> {
    let pool = PgPool::connect(connection_string).await?;
    let repo = OffersRepository::new(pool);
    repo.init_db().await?;
    Ok(repo)
}
