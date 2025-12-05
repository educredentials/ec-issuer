//! PostgreSQL Repository Adapter
//!
//! Implements the CredentialRepository port using SQLx and PostgreSQL

use async_trait::async_trait;
use credential_domain::{Credential, DomainError, DomainResult};
use credential_ports::{CredentialRepository, ListFilters};
use sqlx::{PgPool, Row};
use uuid::Uuid;

pub struct PostgresCredentialRepository {
    pool: PgPool,
}

impl PostgresCredentialRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Initialize database schema
    pub async fn migrate(&self) -> Result<(), sqlx::Error> {
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS credentials (
                id UUID PRIMARY KEY,
                subject_id TEXT NOT NULL,
                subject_data JSONB NOT NULL,
                achievement_id TEXT NOT NULL,
                achievement_data JSONB NOT NULL,
                issuer_id TEXT NOT NULL,
                issuer_data JSONB NOT NULL,
                status TEXT NOT NULL,
                issued_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ,
                revocation_info JSONB,
                proof JSONB,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_credentials_subject_id ON credentials(subject_id);
            CREATE INDEX IF NOT EXISTS idx_credentials_issuer_id ON credentials(issuer_id);
            CREATE INDEX IF NOT EXISTS idx_credentials_achievement_id ON credentials(achievement_id);
            CREATE INDEX IF NOT EXISTS idx_credentials_status ON credentials(status);
            CREATE INDEX IF NOT EXISTS idx_credentials_created_at ON credentials(created_at);
            "#,
        )
        .execute(&self.pool)
        .await?;

        Ok(())
    }
}

#[async_trait]
impl CredentialRepository for PostgresCredentialRepository {
    async fn save(&self, credential: &Credential) -> DomainResult<()> {
        let subject_data = serde_json::to_value(&credential.credential_subject)
            .map_err(|e| DomainError::serialization_error(e.to_string()))?;

        let achievement_data = serde_json::to_value(&credential.achievement)
            .map_err(|e| DomainError::serialization_error(e.to_string()))?;

        let issuer_data = serde_json::to_value(&credential.issuer)
            .map_err(|e| DomainError::serialization_error(e.to_string()))?;

        sqlx::query(
            r#"
            INSERT INTO credentials (
                id, subject_id, subject_data, achievement_id, achievement_data,
                issuer_id, issuer_data, status, issued_at, expires_at,
                revocation_info, proof, metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            "#,
        )
        .bind(credential.id)
        .bind(&credential.credential_subject.id)
        .bind(subject_data)
        .bind(&credential.achievement.id)
        .bind(achievement_data)
        .bind(&credential.issuer.id)
        .bind(issuer_data)
        .bind(credential.status.to_string())
        .bind(credential.issued_at)
        .bind(credential.expires_at)
        .bind(credential.revocation_info)
        .bind(&credential.proof)
        .bind(&credential.metadata)
        .bind(credential.created_at)
        .bind(credential.updated_at)
        .execute(&self.pool)
        .await
        .map_err(|e| DomainError::serialization_error(format!("Database error: {}", e)))?;

        Ok(())
    }

    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Credential>> {
        let row = sqlx::query(
            r#"
            SELECT id, subject_data, achievement_data, issuer_data, status,
                   issued_at, expires_at, revocation_info, proof, metadata,
                   created_at, updated_at
            FROM credentials
            WHERE id = $1
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::serialization_error(format!("Database error: {}", e)))?;

        if let Some(row) = row {
            let credential = Credential {
                id: row.get("id"),
                credential_subject: serde_json::from_value(row.get("subject_data"))
                    .map_err(|e| DomainError::serialization_error(e.to_string()))?,
                achievement: serde_json::from_value(row.get("achievement_data"))
                    .map_err(|e| DomainError::serialization_error(e.to_string()))?,
                issuer: serde_json::from_value(row.get("issuer_data"))
                    .map_err(|e| DomainError::serialization_error(e.to_string()))?,
                status: row
                    .get::<String, _>("status")
                    .parse()
                    .map_err(|e: DomainError| e)?,
                issued_at: row.get("issued_at"),
                expires_at: row.get("expires_at"),
                revocation_info: row.get("revocation_info"),
                proof: row.get("proof"),
                metadata: row.get("metadata"),
                created_at: row.get("created_at"),
                updated_at: row.get("updated_at"),
            };

            Ok(Some(credential))
        } else {
            Ok(None)
        }
    }

    async fn update(&self, credential: &Credential) -> DomainResult<()> {
        let subject_data = serde_json::to_value(&credential.credential_subject)
            .map_err(|e| DomainError::serialization_error(e.to_string()))?;

        let achievement_data = serde_json::to_value(&credential.achievement)
            .map_err(|e| DomainError::serialization_error(e.to_string()))?;

        let issuer_data = serde_json::to_value(&credential.issuer)
            .map_err(|e| DomainError::serialization_error(e.to_string()))?;

        sqlx::query(
            r#"
            UPDATE credentials
            SET subject_data = $2, achievement_data = $3, issuer_data = $4,
                status = $5, expires_at = $6, revocation_info = $7,
                proof = $8, metadata = $9, updated_at = $10
            WHERE id = $1
            "#,
        )
        .bind(credential.id)
        .bind(subject_data)
        .bind(achievement_data)
        .bind(issuer_data)
        .bind(credential.status.to_string())
        .bind(credential.expires_at)
        .bind(&credential.revocation_info)
        .bind(&credential.proof)
        .bind(&credential.metadata)
        .bind(credential.updated_at)
        .execute(&self.pool)
        .await
        .map_err(|e| DomainError::serialization_error(format!("Database error: {}", e)))?;

        Ok(())
    }

    async fn list(&self, filters: ListFilters) -> DomainResult<(Vec<Credential>, i64)> {
        let mut query = String::from(
            r#"
            SELECT id, subject_data, achievement_data, issuer_data, status,
                   issued_at, expires_at, revocation_info, proof, metadata,
                   created_at, updated_at
            FROM credentials
            WHERE 1=1
            "#,
        );

        let mut bindings = Vec::new();
        let mut param_count = 1;

        if let Some(subject_id) = &filters.subject_id {
            query.push_str(&format!(" AND subject_id = ${}", param_count));
            bindings.push(subject_id.clone());
            param_count += 1;
        }

        if let Some(issuer_id) = &filters.issuer_id {
            query.push_str(&format!(" AND issuer_id = ${}", param_count));
            bindings.push(issuer_id.clone());
            param_count += 1;
        }

        if let Some(achievement_id) = &filters.achievement_id {
            query.push_str(&format!(" AND achievement_id = ${}", param_count));
            bindings.push(achievement_id.clone());
            param_count += 1;
        }

        if let Some(status) = &filters.status {
            query.push_str(&format!(" AND status = ${}", param_count));
            bindings.push(status.clone());
            param_count += 1;
        }

        query.push_str(" ORDER BY created_at DESC");

        if let Some(limit) = filters.limit {
            query.push_str(&format!(" LIMIT ${}", param_count));
            param_count += 1;
            bindings.push(limit.to_string());
        }

        if let Some(offset) = filters.offset {
            query.push_str(&format!(" OFFSET ${}", param_count));
            bindings.push(offset.to_string());
        }

        // Execute query - simplified version (proper implementation would use query builder)
        let mut sql_query = sqlx::query(&query);
        for binding in &bindings {
            sql_query = sql_query.bind(binding);
        }

        let rows = sql_query
            .fetch_all(&self.pool)
            .await
            .map_err(|e| DomainError::serialization_error(format!("Database error: {}", e)))?;

        let credentials: Result<Vec<Credential>, DomainError> = rows
            .into_iter()
            .map(|row| {
                Ok(Credential {
                    id: row.get("id"),
                    credential_subject: serde_json::from_value(row.get("subject_data"))
                        .map_err(|e| DomainError::serialization_error(e.to_string()))?,
                    achievement: serde_json::from_value(row.get("achievement_data"))
                        .map_err(|e| DomainError::serialization_error(e.to_string()))?,
                    issuer: serde_json::from_value(row.get("issuer_data"))
                        .map_err(|e| DomainError::serialization_error(e.to_string()))?,
                    status: row
                        .get::<String, _>("status")
                        .parse()
                        .map_err(|e: DomainError| e)?,
                    issued_at: row.get("issued_at"),
                    expires_at: row.get("expires_at"),
                    revocation_info: row.get("revocation_info"),
                    proof: row.get("proof"),
                    metadata: row.get("metadata"),
                    created_at: row.get("created_at"),
                    updated_at: row.get("updated_at"),
                })
            })
            .collect();

        let credentials = credentials?;
        let total = credentials.len() as i64;

        Ok((credentials, total))
    }

    async fn delete(&self, id: Uuid) -> DomainResult<()> {
        sqlx::query("DELETE FROM credentials WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await
            .map_err(|e| DomainError::serialization_error(format!("Database error: {}", e)))?;

        Ok(())
    }
}
