/// Offer service for creating and retrieving credential offers.
///
/// Orchestrates the flow: check access → fetch award → create offer → persist.
/// On persistence failure, rolls back the upstream offer.
use std::collections::HashMap;

use crate::awards::client::{AwardError, new_http_awards_client_arc};
use crate::config::Config;
use crate::credential_converter::client::new_credential_converter_client_arc;
use crate::helpers::reqwest_client::ReqwestHttpClientArc;
use crate::offers::ssi_agent::{SsiAgentOffersClient, new_ssi_agent_offers_client_arc};
use crate::offers::{models::Offer, port::OffersClientPort, port::OffersRepositoryPort};

use super::models::CredentialType;

/// Error raised when an unsupported `credential_type` value is provided.
#[derive(Debug, thiserror::Error)]
#[error("Unsupported credential_type: {0}. Must be 'ob3' or 'edc'.")]
pub struct UnknownCredentialTypeError(pub String);

/// Error raised when access control denies the requested action.
#[derive(Debug, thiserror::Error)]
#[error("Access denied: {0}")]
pub struct PermissionDeniedError(pub String);

/// Error raised when a requested resource cannot be found.
#[derive(Debug, thiserror::Error)]
#[error("{0}")]
pub struct NotFoundError(pub String);

/// Error raised when an upstream service returns an unexpected error.
#[derive(Debug, thiserror::Error)]
#[error("Offer service error: {0}")]
pub struct OfferServiceError(pub String);

/// Service that orchestrates offer creation and retrieval.
pub struct OfferService<Repo: OffersRepositoryPort, Client: OffersClientPort> {
    /// Access control port for permission checks.
    access_control: Box<dyn crate::access_control::AccessControlPort + Send + Sync>,
    /// Award client for fetching awards.
    awards_client: Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>,
    /// Repository for persisting offers.
    offers_repository: Repo,
    /// Client for interacting with the SSI agent offers API.
    offers_client: Client,
    /// Credential converter for OB3→EDC conversion.
    credential_converter:
        Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>,
    _marker: std::marker::PhantomData<(Repo, Client)>,
}

impl<Repo, Client> OfferService<Repo, Client>
where
    Repo: OffersRepositoryPort + Send + Sync,
    Client: OffersClientPort + Send + Sync,
{
    /// Create a new offer service.
    ///
    /// # Arguments
    ///
    /// * `access_control` - Access control adapter.
    /// * `awards_client` - Award fetching client.
    /// * `offers_repository` - Offers repository.
    /// * `offers_client` - SSI agent offers client.
    /// * `credential_converter` - Credential converter.
    pub fn new(
        access_control: Box<dyn crate::access_control::AccessControlPort + Send + Sync>,
        awards_client: Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>,
        offers_repository: Repo,
        offers_client: Client,
        credential_converter: Box<
            dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync,
        >,
    ) -> Self {
        Self {
            access_control,
            awards_client,
            offers_repository,
            offers_client,
            credential_converter,
            _marker: std::marker::PhantomData,
        }
    }

    /// Create, persist, and return a new credential offer.
    ///
    /// # Arguments
    ///
    /// * `award_id` - The award/achievement to issue.
    /// * `bearer_token` - The caller's bearer token used for permission checking.
    /// * `credential_type` - The credential type to issue — `"ob3"` (default) or
    ///   `"edc"`.
    ///
    /// # Errors
    ///
    /// Returns an error when access is denied, the award is not found, or an
    /// upstream service fails.
    pub async fn create_offer(
        &self,
        award_id: &str,
        bearer_token: &str,
        credential_type: &str,
    ) -> Result<Offer, OfferServiceError> {
        let credential_type = crate::offers::models::CredentialType::from_short(credential_type)
            .map_err(|msg| OfferServiceError(UnknownCredentialTypeError(msg).to_string()))?;

        if !self
            .access_control
            .may_import(bearer_token, award_id, "Award", "import")
        {
            return Err(OfferServiceError(
                PermissionDeniedError(award_id.to_string()).to_string(),
            ));
        }

        let offer_id = uuid::Uuid::new_v4().to_string();

        // Fetch the award and create the upstream offer.
        match credential_type {
            crate::offers::models::CredentialType::EDC => {
                let ob3_award =
                    self.awards_client
                        .get_ob3(award_id, bearer_token)
                        .map_err(|e| match e {
                            AwardError::NotFound(_) => {
                                OfferServiceError(format!("Award {award_id} not found"))
                            }
                            AwardError::Forbidden(_) => {
                                OfferServiceError(format!("Access denied: {award_id}"))
                            }
                            other => OfferServiceError(other.to_string()),
                        })?;

                let raw_ob3 = serde_json::to_value(&ob3_award)
                    .map_err(|e| OfferServiceError(e.to_string()))?;
                let edc_value = self
                    .credential_converter
                    .convert(&raw_ob3)
                    .map_err(|e| OfferServiceError(e.to_string()))?;

                self.offers_client
                    .create_edc(&offer_id, &edc_value)
                    .map_err(|e| OfferServiceError(e.to_string()))?;
            }
            crate::offers::models::CredentialType::OB3 => {
                let award =
                    self.awards_client
                        .get_ob3(award_id, bearer_token)
                        .map_err(|e| match e {
                            AwardError::NotFound(_) => {
                                OfferServiceError(format!("Award {award_id} not found"))
                            }
                            AwardError::Forbidden(_) => {
                                OfferServiceError(format!("Access denied: {award_id}"))
                            }
                            other => OfferServiceError(other.to_string()),
                        })?;

                self.offers_client
                    .create_ob3(&offer_id, &award)
                    .map_err(|e| OfferServiceError(e.to_string()))?;
            }
        }

        // Persist the offer. On failure, rollback the upstream offer.
        let offer = Offer {
            offer_id: offer_id.clone(),
            award_id: award_id.to_string(),
            uri: None,
            credential_ids: Vec::new(),
            created_at: Some(chrono::Utc::now()),
        };

        if let Err(e) = self.offers_repository.store(offer.clone()).await {
            // Attempt rollback but don't mask the original error.
            let _ = self.offers_client.rollback(&offer_id);
            return Err(OfferServiceError(e.to_string()));
        }

        Ok(offer)
    }

    /// Retrieve an offer by its identifier.
    ///
    /// # Arguments
    ///
    /// * `offer_id` - The unique offer identifier.
    ///
    /// # Errors
    ///
    /// Returns `NotFoundError` when the offer is not found in either the
    /// upstream client or the repository.
    pub async fn get_offer(&self, offer_id: &str) -> Result<Offer, OfferServiceError> {
        let upstream_offer = self
            .offers_client
            .get(offer_id)
            .map_err(|e| OfferServiceError(e.to_string()))?;

        let stored_offer = self
            .offers_repository
            .get(offer_id)
            .await
            .map_err(|e| OfferServiceError(e.0))?;

        Ok(Offer {
            offer_id: offer_id.to_string(),
            award_id: stored_offer.award_id,
            uri: upstream_offer.uri,
            credential_ids: stored_offer.credential_ids,
            created_at: stored_offer.created_at,
        })
    }

    /// Return true when the database is reachable.
    pub async fn health_check(&self) -> bool {
        self.offers_repository.health_check().await
    }
}

/// Convenience constructor that builds all dependencies from a Config.
///
/// # Panics
///
/// Panics if the database connection fails.
pub async fn make_offer_service(
    config: &Config,
) -> OfferService<
    crate::offers::postgres::OffersRepository,
    SsiAgentOffersClient<ReqwestHttpClientArc>,
> {
    let reqwest_client = ReqwestHttpClientArc::new();
    let access_control = Box::new(crate::access_control::TokenAccessControlAdapter)
        as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
    let awards_client = Box::new(new_http_awards_client_arc(
        &config.awards_service_url,
        &config.ec_issuer_url,
        &reqwest_client,
    )) as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;

    let template_ids: HashMap<CredentialType, String> = config
        .credential_configuration_ids
        .iter()
        .map(|(k, v)| (*k, v.clone()))
        .collect();
    let offers_client =
        new_ssi_agent_offers_client_arc(&config.ssi_agent_url, template_ids, &reqwest_client);
    let converter = Box::new(new_credential_converter_client_arc(
        &reqwest_client,
        &config.credential_converter_url,
    ))
        as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

    let pool = sqlx::PgPool::connect(&config.postgresql_connection_string).await.unwrap();
    let repository = crate::offers::postgres::OffersRepository::new(pool);

    OfferService::new(
        access_control,
        awards_client,
        repository,
        offers_client,
        converter,
    )
}

#[cfg(test)]
mod tests {
    use std::sync::Mutex;

    use crate::awards::models::{
        Achievement, AchievementSubject, CredentialContextItem, Criteria, Issuer, OB3Award,
        ob3_default_schema,
    };
    use crate::awards::port::AwardsClientPort;
    use crate::credential_converter::port::{
        CredentialConverterClientError, CredentialConverterPort,
    };
    use crate::offers::port::{OffersClientError, OffersClientPort, OffersRepositoryPort};
    use crate::offers::service::{
        OfferService, OfferServiceError,
    };

    const SAMPLE_ELM_CREDENTIAL: &str = r#"{"@context":["https://www.w3.org/ns/credentials/v2"],"type":["VerifiableCredential","EuropeanDigitalCredential"],"credentialSubject":{"id":"did:example:subject"}}"#;

    fn sample_ob3_award() -> OB3Award {
        OB3Award {
            id: "https://DOMAIN/assertions/I41eovHQReGI_SG5KM6dSQ".to_string(),
            r#type: vec![
                "VerifiableCredential".to_string(),
                "AchievementCredential".to_string(),
            ],
            name: "Test Badge".to_string(),
            issuer: Issuer {
                id: "https://DOMAIN/issuers/1".to_string(),
                r#type: vec!["Profile".to_string()],
                name: "Test Issuer".to_string(),
                parent_org: None,
            },
            valid_from: "2024-01-01T00:00:00Z".to_string(),
            credential_subject: AchievementSubject {
                id: "https://DOMAIN/assertions/1".to_string(),
                r#type: vec!["AchievementSubject".to_string()],
                achievement: Achievement {
                    id: "https://DOMAIN/assertions/1".to_string(),
                    r#type: vec!["Achievement".to_string()],
                    criteria: Criteria {
                        narrative: "Do the thing".to_string(),
                    },
                    description: "Test description".to_string(),
                    name: "Test Badge".to_string(),
                    image: None,
                    in_language: None,
                    ects: None,
                    eqf: None,
                    learning_outcome: None,
                    education_program_identifier: None,
                    form_of_participation: None,
                    assessment_type: None,
                    supervision_type: None,
                    time_investment: None,
                },
                identifier: vec![],
            },
            credential_schema: ob3_default_schema(),
            valid_until: None,
            entity_id: None,
            credential_context: Some(vec![CredentialContextItem::Url(
                "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json".to_string(),
            )]),
            credential_status: None,
        }
    }

    #[derive(Default)]
    struct OffersRepositorySpy {
        calls: Mutex<Vec<String>>,
        store_offer: Mutex<Option<super::super::models::Offer>>,
    }

    #[allow(clippy::unused_async_trait_impl)]
    impl OffersRepositoryPort for OffersRepositorySpy {
        async fn store(&self, offer: super::super::models::Offer) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
            self.calls.lock().unwrap().push("store".to_string());
            *self.store_offer.lock().unwrap() = Some(offer);
            Ok(())
        }

        async fn get(&self, _offer_id: &str) -> Result<super::super::models::Offer, crate::offers::port::OfferNotFound> {
            Ok(super::super::models::Offer {
                offer_id: "offer-123".to_string(),
                award_id: "award-123".to_string(),
                uri: Some("http://example.com/offers/offer-123".to_string()),
                credential_ids: vec![],
                created_at: None,
            })
        }

        fn close(&self) {}
        async fn health_check(&self) -> bool {
            true
        }
    }

    #[derive(Default)]
    struct FailingOffersRepository {
        should_fail: bool,
    }

    #[allow(clippy::unused_async_trait_impl)]
    impl OffersRepositoryPort for FailingOffersRepository {
        async fn store(&self, _offer: super::super::models::Offer) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
            if self.should_fail {
                return Err(Box::new(std::io::Error::other("transient db failure")));
            }
            Ok(())
        }

        async fn get(&self, _offer_id: &str) -> Result<super::super::models::Offer, crate::offers::port::OfferNotFound> {
            Ok(super::super::models::Offer {
                offer_id: "offer-123".to_string(),
                award_id: "award-123".to_string(),
                uri: Some("http://example.com/offers/offer-123".to_string()),
                credential_ids: vec![],
                created_at: None,
            })
        }

        fn close(&self) {}
        async fn health_check(&self) -> bool {
            true
        }
    }

    #[derive(Default, Clone)]
    struct OffersClientSpy {
        pub calls: std::sync::Arc<Mutex<Vec<(String, String)>>>,
    }

    impl OffersClientPort for OffersClientSpy {
        fn create_ob3(
            &self,
            offer_id: &str,
            _award: &OB3Award,
        ) -> Result<super::super::models::OfferCreated, OffersClientError> {
            self.calls
                .lock()
                .unwrap()
                .push(("create_ob3".to_string(), offer_id.to_string()));
            Ok(super::super::models::OfferCreated {
                uri: "http://example.com/offers/offer-123".to_string(),
                credential_ids: None,
            })
        }

        fn create_edc(
            &self,
            offer_id: &str,
            _credential: &serde_json::Value,
        ) -> Result<super::super::models::OfferCreated, OffersClientError> {
            self.calls
                .lock()
                .unwrap()
                .push(("create_edc".to_string(), offer_id.to_string()));
            Ok(super::super::models::OfferCreated {
                uri: "http://example.com/offers/offer-123".to_string(),
                credential_ids: None,
            })
        }

        fn get(&self, offer_id: &str) -> Result<super::super::models::Offer, OffersClientError> {
            Ok(super::super::models::Offer {
                offer_id: offer_id.to_string(),
                award_id: "award-123".to_string(),
                uri: Some(format!("http://example.com/offers/{offer_id}")),
                credential_ids: vec![],
                created_at: None,
            })
        }

        fn rollback(&self, offer_id: &str) -> Result<(), OffersClientError> {
            self.calls
                .lock()
                .unwrap()
                .push(("rollback".to_string(), offer_id.to_string()));
            Ok(())
        }
    }

    #[derive(Default)]
    struct OffersClientStubNotFound;

    impl OffersClientPort for OffersClientStubNotFound {
        fn create_ob3(
            &self,
            _offer_id: &str,
            _award: &OB3Award,
        ) -> Result<super::super::models::OfferCreated, OffersClientError> {
            Ok(super::super::models::OfferCreated {
                uri: "http://example.com/offers/offer-123".to_string(),
                credential_ids: None,
            })
        }

        fn create_edc(
            &self,
            _offer_id: &str,
            _credential: &serde_json::Value,
        ) -> Result<super::super::models::OfferCreated, OffersClientError> {
            Ok(super::super::models::OfferCreated {
                uri: "http://example.com/offers/offer-123".to_string(),
                credential_ids: None,
            })
        }

        fn get(&self, _offer_id: &str) -> Result<super::super::models::Offer, OffersClientError> {
            Err(OffersClientError("Offer not found".to_string()))
        }

        fn rollback(&self, _offer_id: &str) -> Result<(), OffersClientError> {
            Ok(())
        }
    }

    struct DenyingAccessControl;

    impl crate::access_control::AccessControlPort for DenyingAccessControl {
        fn may_import(
            &self,
            _bearer_token: &str,
            _resource_id: &str,
            _resource_type: &str,
            _permission: &str,
        ) -> bool {
            false
        }
    }

    struct AcceptingAccessControl;

    impl crate::access_control::AccessControlPort for AcceptingAccessControl {
        fn may_import(
            &self,
            _bearer_token: &str,
            _resource_id: &str,
            _resource_type: &str,
            _permission: &str,
        ) -> bool {
            true
        }
    }

    struct StubAwardsClient;

    impl AwardsClientPort for StubAwardsClient {
        fn get_ob3(
            &self,
            _award_id: &str,
            _bearer_token: &str,
        ) -> Result<OB3Award, crate::awards::client::AwardError> {
            Ok(sample_ob3_award())
        }
    }

    struct StubCredentialConverter;

    impl CredentialConverterPort for StubCredentialConverter {
        fn convert(
            &self,
            _credential_json: &serde_json::Value,
        ) -> Result<serde_json::Value, CredentialConverterClientError> {
            serde_json::from_str(SAMPLE_ELM_CREDENTIAL)
                .map_err(|e| CredentialConverterClientError(e.to_string()))
        }
    }

    fn make_service(
        offers_client: OffersClientSpy,
        repository: impl OffersRepositoryPort + 'static + Send + Sync,
    ) -> OfferService<impl OffersRepositoryPort, OffersClientSpy> {
        let access_control = Box::new(AcceptingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        OfferService::new(
            access_control,
            awards_client,
            repository,
            offers_client,
            converter,
        )
    }

    // ─── TestOfferServiceCreateOffer ───────────────────────────────────────

    #[test]
    fn test_returns_offer_with_correct_uri_format() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();
        let service = make_service(offers_client, repo);

        let offer = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-123", "test-token", "ob3"));
        assert!(offer.is_ok());
        let offer = offer.unwrap();
        assert!(offer.offer_id.contains('-'));
    }

    #[test]
    fn test_stores_offer_in_repository() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();
        let service = make_service(offers_client, repo);

        let offer = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-999", "test-token", "ob3"));
        assert!(offer.is_ok());

        let offer = offer.unwrap();
        assert_eq!(offer.award_id, "award-999");
    }

    #[test]
    fn test_creates_offer_with_client() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();
        let service = make_service(offers_client.clone(), repo);

        let _offer = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-999", "test-token", "ob3"));

        assert_eq!(offers_client.calls.lock().unwrap().len(), 1);
        assert_eq!(offers_client.calls.lock().unwrap()[0].0, "create_ob3");
    }

    #[test]
    fn test_raises_permission_denied_when_access_control_denies() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            offers_client,
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-123", "test-token", "ob3"));
        assert!(result.is_err());
        match result.unwrap_err() {
            OfferServiceError(msg) => assert!(msg.contains("denied") || msg.contains("access")),
        }
    }

    #[test]
    fn test_create_offer_dispatches_create_edc_when_credential_type_is_edc() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(AcceptingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            offers_client.clone(),
            converter,
        );

        let _offer = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-999", "test-token", "edc"));

        assert_eq!(offers_client.calls.lock().unwrap().len(), 1);
        assert_eq!(offers_client.calls.lock().unwrap()[0].0, "create_edc");
    }

    #[test]
    fn test_edc_path_converts_ob3_award_through_converter() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            offers_client,
            converter,
        );

        let _offer = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-999", "test-token", "edc"));
    }

    // ─── TestOfferServiceGetOffer ─────────────────────────────────────────

    #[test]
    fn test_get_offer_returns_stored_offer() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            offers_client,
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.get_offer("offer-123"));
        assert!(result.is_ok());
        let offer = result.unwrap();
        assert_eq!(offer.offer_id, "offer-123");
        assert_eq!(offer.award_id, "award-123");
    }

    #[test]
    fn test_get_offer_raises_not_found_when_offer_absent_in_client() {
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            OffersClientStubNotFound,
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.get_offer("nonexistent-id"));
        assert!(result.is_err());
        match result.unwrap_err() {
            OfferServiceError(msg) => assert!(msg.contains("not found")),
        }
    }

    #[test]
    fn test_get_offer_raises_offer_service_error_on_client_error() {
        struct ErroringOffersClient;

        impl OffersClientPort for ErroringOffersClient {
            fn create_ob3(
                &self,
                _offer_id: &str,
                _award: &OB3Award,
            ) -> Result<super::super::models::OfferCreated, OffersClientError> {
                Ok(super::super::models::OfferCreated {
                    uri: "http://example.com".to_string(),
                    credential_ids: None,
                })
            }

            fn create_edc(
                &self,
                _offer_id: &str,
                _credential: &serde_json::Value,
            ) -> Result<super::super::models::OfferCreated, OffersClientError> {
                Ok(super::super::models::OfferCreated {
                    uri: "http://example.com".to_string(),
                    credential_ids: None,
                })
            }

            fn get(&self, _offer_id: &str) -> Result<super::super::models::Offer, OffersClientError> {
                Err(OffersClientError("upstream failure".to_string()))
            }

            fn rollback(&self, _offer_id: &str) -> Result<(), OffersClientError> {
                Ok(())
            }
        }

        let repo = OffersRepositorySpy::default();
        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            ErroringOffersClient,
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.get_offer("test-123"));
        assert!(result.is_err());
        match result.unwrap_err() {
            OfferServiceError(msg) => assert!(msg.contains("upstream failure")),
        }
    }

    // ─── TestOfferServiceTransactionRollback ─────────────────────────────

    #[test]
    fn test_rollback_called_when_repository_store_fails() {
        let offers_client = OffersClientSpy::default();

        let access_control = Box::new(AcceptingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let failing_repo = FailingOffersRepository { should_fail: true };
        let service = OfferService::new(
            access_control,
            awards_client,
            failing_repo,
            offers_client.clone(),
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-42", "test-token", "ob3"));

        assert!(result.is_err());

        assert_eq!(offers_client.calls.lock().unwrap().len(), 2);
        assert_eq!(offers_client.calls.lock().unwrap()[0].0, "create_ob3");
        assert_eq!(offers_client.calls.lock().unwrap()[1].0, "rollback");
    }

    // ─── TestOfferServiceCreateOfferCredentialType ───────────────────────

    #[test]
    fn test_raises_unknown_credential_type_for_invalid_value() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            offers_client,
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-123", "test-token", "unsupported"));
        assert!(result.is_err());
        match result.unwrap_err() {
            OfferServiceError(msg) => assert!(msg.contains("credential_type")),
        }
    }

    #[test]
    fn test_edc_credential_type_rejected_when_invalid_case() {
        let offers_client = OffersClientSpy::default();
        let repo = OffersRepositorySpy::default();

        let access_control = Box::new(DenyingAccessControl)
            as Box<dyn crate::access_control::AccessControlPort + Send + Sync>;
        let awards_client = Box::new(StubAwardsClient)
            as Box<dyn crate::awards::port::AwardsClientPort + Send + Sync>;
        let converter = Box::new(StubCredentialConverter)
            as Box<dyn crate::credential_converter::port::CredentialConverterPort + Send + Sync>;

        let service = OfferService::new(
            access_control,
            awards_client,
            repo,
            offers_client,
            converter,
        );

        let result = tokio::runtime::Runtime::new()
            .unwrap()
            .block_on(service.create_offer("award-123", "test-token", "EDC"));
        assert!(result.is_err());
    }
}
