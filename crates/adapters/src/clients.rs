//! External Client Adapters
//!
//! Implements ports for fetching achievement and issuer information

use async_trait::async_trait;
use credential_domain::{Achievement, DomainError, DomainResult, Issuer};
use credential_ports::{AchievementClient, IssuerClient};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// In-memory achievement client (for testing/demo)
pub struct InMemoryAchievementClient {
    achievements: Arc<RwLock<HashMap<String, Achievement>>>,
}

impl InMemoryAchievementClient {
    pub fn new() -> Self {
        let mut achievements = HashMap::new();

        // Add some sample achievements
        achievements.insert(
            "achievement-1".to_string(),
            Achievement::new(
                "https://example.com/achievements/1",
                "Digital Literacy Certificate",
                "Demonstrates proficiency in digital literacy skills",
            )
            .with_criteria("Complete all digital literacy modules"),
        );

        achievements.insert(
            "achievement-2".to_string(),
            Achievement::new(
                "https://example.com/achievements/2",
                "Leadership Badge",
                "Demonstrates leadership capabilities",
            )
            .with_criteria("Complete leadership training program"),
        );

        Self {
            achievements: Arc::new(RwLock::new(achievements)),
        }
    }

    pub async fn add_achievement(&self, id: String, achievement: Achievement) {
        let mut achievements = self.achievements.write().await;
        achievements.insert(id, achievement);
    }
}

impl Default for InMemoryAchievementClient {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl AchievementClient for InMemoryAchievementClient {
    async fn get_achievement(&self, id: &str) -> DomainResult<Achievement> {
        let achievements = self.achievements.read().await;
        achievements
            .get(id)
            .cloned()
            .ok_or_else(|| DomainError::achievement_not_found(id))
    }
}

/// In-memory issuer client (for testing/demo)
pub struct InMemoryIssuerClient {
    issuers: Arc<RwLock<HashMap<String, Issuer>>>,
}

impl InMemoryIssuerClient {
    pub fn new() -> Self {
        let mut issuers = HashMap::new();

        // Add some sample issuers
        issuers.insert(
            "issuer-1".to_string(),
            Issuer::new("https://example.com/issuers/1", "Example University")
                .with_url("https://example.com")
                .with_email("credentials@example.com"),
        );

        issuers.insert(
            "issuer-2".to_string(),
            Issuer::new("https://example.com/issuers/2", "Certification Authority")
                .with_url("https://certauth.example.com")
                .with_email("info@certauth.example.com"),
        );

        Self {
            issuers: Arc::new(RwLock::new(issuers)),
        }
    }

    pub async fn add_issuer(&self, id: String, issuer: Issuer) {
        let mut issuers = self.issuers.write().await;
        issuers.insert(id, issuer);
    }
}

impl Default for InMemoryIssuerClient {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl IssuerClient for InMemoryIssuerClient {
    async fn get_issuer(&self, id: &str) -> DomainResult<Issuer> {
        let issuers = self.issuers.read().await;
        issuers
            .get(id)
            .cloned()
            .ok_or_else(|| DomainError::issuer_not_found(id))
    }
}

/// HTTP-based achievement client (for production use)
pub struct HttpAchievementClient {
    base_url: String,
    client: reqwest::Client,
}

impl HttpAchievementClient {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: reqwest::Client::new(),
        }
    }
}

#[async_trait]
impl AchievementClient for HttpAchievementClient {
    async fn get_achievement(&self, id: &str) -> DomainResult<Achievement> {
        let url = format!("{}/achievements/{}", self.base_url, id);

        let response = self
            .client
            .get(&url)
            .send()
            .await
            .map_err(|e| DomainError::serialization_error(format!("HTTP error: {}", e)))?;

        if response.status().is_success() {
            response
                .json::<Achievement>()
                .await
                .map_err(|e| DomainError::serialization_error(format!("JSON error: {}", e)))
        } else {
            Err(DomainError::achievement_not_found(id))
        }
    }
}

/// HTTP-based issuer client (for production use)
pub struct HttpIssuerClient {
    base_url: String,
    client: reqwest::Client,
}

impl HttpIssuerClient {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: reqwest::Client::new(),
        }
    }
}

#[async_trait]
impl IssuerClient for HttpIssuerClient {
    async fn get_issuer(&self, id: &str) -> DomainResult<Issuer> {
        let url = format!("{}/issuers/{}", self.base_url, id);

        let response = self
            .client
            .get(&url)
            .send()
            .await
            .map_err(|e| DomainError::serialization_error(format!("HTTP error: {}", e)))?;

        if response.status().is_success() {
            response
                .json::<Issuer>()
                .await
                .map_err(|e| DomainError::serialization_error(format!("JSON error: {}", e)))
        } else {
            Err(DomainError::issuer_not_found(id))
        }
    }
}
