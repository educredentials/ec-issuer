/// Postgres connection base.
use sqlx::PgPool;

/// Postgres connection pool handle.
pub struct PgBase {
    /// Database connection pool.
    pub pool: PgPool,
}

impl PgBase {
    /// Create a new Postgres connection pool.
    ///
    /// # Arguments
    ///
    /// * `connection_string` - PostgreSQL connection string.
    ///
    /// # Errors
    ///
    /// Returns `sqlx::Error` if the connection string is invalid or the
    /// database is unreachable.
    pub async fn new(connection_string: &str) -> Result<Self, sqlx::Error> {
        let pool = PgPool::connect(connection_string).await?;
        Ok(Self { pool })
    }

    /// Return true when the database is reachable.
    ///
    /// # Errors
    ///
    /// Returns `sqlx::Error` if the connection pool is closed or the
    /// database is unreachable.
    pub async fn health_check(&self) -> Result<(), sqlx::Error> {
        sqlx::query("SELECT 1").execute(&self.pool).await?;
        Ok(())
    }
}
