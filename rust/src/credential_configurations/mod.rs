/// Credential configurations module.
use crate::helpers::http_client::HttpClientError;

pub mod bootstrap;
pub mod models;
pub mod ssi_agent;

/// Port: interface for credential template operations.
///
/// This trait exists so that tests can mock credential template operations
/// without involving a real HTTP client.
pub trait CredentialTemplateClientPort {
    /// Create a new credential template.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    fn create(
        &self,
        template: &models::CredentialTemplate,
    ) -> Result<models::CredentialTemplate, HttpClientError>;

    /// List all credential templates.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    fn list(&self) -> Result<Vec<models::CredentialTemplate>, HttpClientError>;

    /// Retrieve a credential template by ID.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    fn get(&self, template_id: &str) -> Result<models::CredentialTemplate, HttpClientError>;

    /// Update an existing credential template.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    fn update(
        &self,
        configuration: &models::CredentialTemplate,
    ) -> Result<models::CredentialTemplate, HttpClientError>;

    /// Delete a credential template by ID.
    ///
    /// # Errors
    ///
    /// Returns `HttpClientError` on HTTP failure.
    fn delete(&self, template_id: &str) -> Result<(), HttpClientError>;
}

/// Find an existing template by title, or create the template.
///
/// Searches for a template with a matching title.
/// If one exists, it is returned. Otherwise the new template is
/// created and the created result is returned.
///
/// # Errors
///
/// Returns `HttpClientError` on HTTP failure.
pub fn ensure_by_title(
    client: &dyn CredentialTemplateClientPort,
    template: &models::CredentialTemplate,
) -> Result<models::CredentialTemplate, HttpClientError> {
    let templates = client.list()?;
    for t in templates {
        if t.title == template.title {
            return Ok(t);
        }
    }
    client.create(template)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::credential_configurations::models::CredentialTemplate;

    fn make_template(title: &str) -> CredentialTemplate {
        CredentialTemplate {
            id: String::new(),
            title: Some(title.to_string()),
            r#type: vec!["VerifiableCredential".to_string()],
            ..Default::default()
        }
    }

    fn empty_template() -> CredentialTemplate {
        CredentialTemplate {
            id: String::new(),
            title: Some(String::new()),
            r#type: vec![],
            ..Default::default()
        }
    }

    struct TestCredentialTemplateClient {
        list_result: Vec<CredentialTemplate>,
        create_result: CredentialTemplate,
    }

    impl CredentialTemplateClientPort for TestCredentialTemplateClient {
        fn create(
            &self,
            _template: &CredentialTemplate,
        ) -> Result<CredentialTemplate, HttpClientError> {
            Ok(self.create_result.clone())
        }

        fn list(&self) -> Result<Vec<CredentialTemplate>, HttpClientError> {
            Ok(self.list_result.clone())
        }

        fn get(&self, _template_id: &str) -> Result<CredentialTemplate, HttpClientError> {
            Ok(CredentialTemplate {
                id: "test-id".to_string(),
                title: Some("test".to_string()),
                ..Default::default()
            })
        }

        fn update(
            &self,
            _configuration: &CredentialTemplate,
        ) -> Result<CredentialTemplate, HttpClientError> {
            Ok(CredentialTemplate {
                id: "updated".to_string(),
                title: Some("updated".to_string()),
                ..Default::default()
            })
        }

        fn delete(&self, _template_id: &str) -> Result<(), HttpClientError> {
            Ok(())
        }
    }

    #[test]
    fn test_returns_existing_when_title_matches() {
        let existing = CredentialTemplate {
            id: "existing-id".to_string(),
            title: Some("Existing".to_string()),
            r#type: vec!["VerifiableCredential".to_string()],
            ..Default::default()
        };
        let client = TestCredentialTemplateClient {
            list_result: vec![existing],
            create_result: make_template("Should Not Be Created"),
        };
        let result = ensure_by_title(&client, &make_template("Existing")).unwrap();

        assert_eq!(result.id, "existing-id");
        assert_eq!(result.title.as_deref(), Some("Existing"));
    }

    #[test]
    fn test_creates_when_no_title_match() {
        let client = TestCredentialTemplateClient {
            list_result: vec![make_template("Other")],
            create_result: CredentialTemplate {
                id: "created-id".to_string(),
                title: Some("New".to_string()),
                r#type: vec!["VerifiableCredential".to_string()],
                ..Default::default()
            },
        };
        let result = ensure_by_title(&client, &make_template("New")).unwrap();

        assert_eq!(result.id, "created-id");
        assert_eq!(result.title.as_deref(), Some("New"));
    }

    #[test]
    fn test_creates_when_list_is_empty() {
        let client = TestCredentialTemplateClient {
            list_result: vec![],
            create_result: CredentialTemplate {
                id: "created-id".to_string(),
                title: Some("New".to_string()),
                r#type: vec!["VerifiableCredential".to_string()],
                ..Default::default()
            },
        };
        let result = ensure_by_title(&client, &make_template("New")).unwrap();

        assert_eq!(result.id, "created-id");
    }

    #[test]
    fn test_returns_existing_even_if_create_would_fail() {
        let existing = CredentialTemplate {
            id: "Found".to_string(),
            title: Some("Found".to_string()),
            r#type: vec!["VerifiableCredential".to_string()],
            ..Default::default()
        };
        let client = TestCredentialTemplateClient {
            list_result: vec![existing],
            create_result: empty_template(),
        };
        let result = ensure_by_title(&client, &make_template("Found")).unwrap();

        assert_eq!(result.id, "Found");
        assert_eq!(result.title.as_deref(), Some("Found"));
    }

    #[test]
    fn test_list_returns_matching_template() {
        let client = TestCredentialTemplateClient {
            list_result: vec![
                make_template("First"),
                make_template("Second"),
                make_template("Match"),
            ],
            create_result: make_template("New"),
        };
        let result = ensure_by_title(&client, &make_template("Match")).unwrap();

        assert_eq!(result.title.as_deref(), Some("Match"));
    }

    #[test]
    fn test_not_found_returns_create_result() {
        let client = TestCredentialTemplateClient {
            list_result: vec![make_template("Other1"), make_template("Other2")],
            create_result: CredentialTemplate {
                id: "new-created".to_string(),
                title: Some("Not Found Title".to_string()),
                r#type: vec!["VerifiableCredential".to_string()],
                ..Default::default()
            },
        };
        let result = ensure_by_title(&client, &make_template("Not Found Title")).unwrap();

        assert_eq!(result.id, "new-created");
        assert_eq!(result.title.as_deref(), Some("Not Found Title"));
    }
}
