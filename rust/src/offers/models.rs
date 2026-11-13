/// Domain models for credential offers.
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Credential type identifiers derived from `dataModel` field values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CredentialType {
    /// Open Badges 3.0.
    #[serde(rename = "open_badges_3-0")]
    OB3,
    /// European Learning Model / European Digital Credentials.
    #[serde(rename = "european_learning_model_v3-3")]
    EDC,
}

impl TryFrom<&str> for CredentialType {
    type Error = String;

    fn try_from(short: &str) -> Result<Self, Self::Error> {
        Self::from_short(short)
    }
}

impl CredentialType {
    /// Parse a short credential type string into a `CredentialType`.
    ///
    /// # Arguments
    ///
    /// * `short` - The short form ("ob3" or "edc").
    ///
    /// # Errors
    ///
    /// Returns an error string for unknown credential types.
    pub fn from_short(short: &str) -> Result<Self, String> {
        match short {
            "ob3" => Ok(Self::OB3),
            "edc" => Ok(Self::EDC),
            other => Err(format!(
                "Unknown short credential type: {other:?}. Must be 'ob3' or 'edc'."
            )),
        }
    }

    /// Resolve a short form (ob3/edc) to the full value.
    ///
    /// # Arguments
    ///
    /// * `short` - The short form credential type.
    ///
    /// # Returns
    ///
    /// The matching `CredentialType` enum value.
    ///
    /// # Panics
    ///
    /// Panics when the short form is not recognised.
    #[must_use]
    pub fn from_short_unchecked(short: &str) -> Self {
        match short {
            "ob3" => Self::OB3,
            "edc" => Self::EDC,
            other => panic!("Unknown short credential type: {other:?}. Must be 'ob3' or 'edc'."),
        }
    }

    /// Validate and coerce a dataModel string to `CredentialType`.
    ///
    /// # Arguments
    ///
    /// * `value` - The dataModel string to validate (e.g. "open_badges_3-0").
    ///
    /// # Returns
    ///
    /// The matching `CredentialType` enum value.
    ///
    /// # Panics
    ///
    /// Panics when the value is not a known credential type.
    #[must_use]
    pub fn from_data_model(value: &str) -> Self {
        match value {
            "open_badges_3-0" => Self::OB3,
            "european_learning_model_v3-3" => Self::EDC,
            other => panic!(
                "Unknown credential type: {other:?}. Must be 'open_badges_3-0' or 'european_learning_model_v3-3'."
            ),
        }
    }
}

/// Domain model representing a credential offer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Offer {
    /// Unique offer identifier.
    pub offer_id: String,
    /// Award/achievement identifier.
    pub award_id: String,
    /// URI pointing to the credential offer.
    pub uri: Option<String>,
    /// Associated credential IDs.
    #[serde(default)]
    pub credential_ids: Vec<String>,
    /// Creation timestamp.
    pub created_at: Option<DateTime<Utc>>,
}

/// Response from creating an offer on the SSI agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OfferCreated {
    /// URI pointing to the credential offer.
    pub uri: String,
    /// Associated credential IDs.
    #[serde(default)]
    pub credential_ids: Option<Vec<String>>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_credential_type_from_short() {
        assert_eq!(CredentialType::from_short("ob3"), Ok(CredentialType::OB3));
        assert_eq!(CredentialType::from_short("edc"), Ok(CredentialType::EDC));
    }

    #[test]
    fn test_credential_type_from_short_unknown() {
        let result = CredentialType::from_short("unknown");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Unknown short credential type"));
    }

    #[test]
    fn test_credential_type_from_short_unchecked() {
        assert_eq!(CredentialType::from_short_unchecked("ob3"), CredentialType::OB3);
        assert_eq!(CredentialType::from_short_unchecked("edc"), CredentialType::EDC);
    }

    #[test]
    #[should_panic(expected = "Unknown short credential type")]
    fn test_credential_type_from_short_unchecked_panics() {
        let _ = CredentialType::from_short_unchecked("unknown");
    }

    #[test]
    fn test_credential_type_from_data_model() {
        assert_eq!(
            CredentialType::from_data_model("open_badges_3-0"),
            CredentialType::OB3,
        );
        assert_eq!(
            CredentialType::from_data_model("european_learning_model_v3-3"),
            CredentialType::EDC,
        );
    }

    #[test]
    #[should_panic(expected = "Unknown credential type")]
    fn test_credential_type_from_data_model_unknown_panics() {
        let _ = CredentialType::from_data_model("unknown_type");
    }

    #[test]
    fn test_offer_creation() {
        let offer = Offer {
            offer_id: "test-offer-id".to_string(),
            award_id: "test-award-id".to_string(),
            uri: Some("http://example.com/offer".to_string()),
            credential_ids: vec!["cred-1".to_string(), "cred-2".to_string()],
            created_at: Some(Utc::now()),
        };

        assert_eq!(offer.offer_id, "test-offer-id");
        assert_eq!(offer.award_id, "test-award-id");
        assert_eq!(offer.uri, Some("http://example.com/offer".to_string()));
        assert_eq!(offer.credential_ids.len(), 2);
    }

    #[test]
    fn test_offer_serialization() {
        let offer = Offer {
            offer_id: "test-offer-id".to_string(),
            award_id: "test-award-id".to_string(),
            uri: Some("http://example.com/offer".to_string()),
            credential_ids: vec![],
            created_at: Some(Utc::now()),
        };

        let json = serde_json::to_string(&offer).expect("Failed to serialize offer");
        assert!(json.contains("test-offer-id"));
        assert!(json.contains("test-award-id"));
    }

    #[test]
    fn test_offer_deserialization() {
        let json = r#"{
            "offer_id": "offer-123",
            "award_id": "award-456",
            "uri": "http://example.com/offer",
            "credential_ids": ["cred-1"],
            "created_at": "2024-01-01T00:00:00+00:00"
        }"#;

        let offer: Offer = serde_json::from_str(json).expect("Failed to deserialize offer");
        assert_eq!(offer.offer_id, "offer-123");
        assert_eq!(offer.award_id, "award-456");
        assert_eq!(offer.uri, Some("http://example.com/offer".to_string()));
        assert_eq!(offer.credential_ids, vec!["cred-1".to_string()]);
    }

    #[test]
    fn test_offer_created_serialization() {
        let created = OfferCreated {
            uri: "http://example.com/offer".to_string(),
            credential_ids: Some(vec!["cred-1".to_string()]),
        };

        let json = serde_json::to_string(&created).expect("Failed to serialize OfferCreated");
        assert!(json.contains("http://example.com/offer"));
        assert!(json.contains("cred-1"));
    }

    #[test]
    fn test_credential_type_serialization() {
        let json = serde_json::to_string(&CredentialType::OB3).expect("Failed to serialize");
        assert_eq!(json, "\"open_badges_3-0\"");

        let json = serde_json::to_string(&CredentialType::EDC).expect("Failed to serialize");
        assert_eq!(json, "\"european_learning_model_v3-3\"");
    }

    #[test]
    fn test_credential_type_deserialization() {
        let ob3: CredentialType =
            serde_json::from_str("\"open_badges_3-0\"").expect("Failed to deserialize");
        assert_eq!(ob3, CredentialType::OB3);

        let edc: CredentialType =
            serde_json::from_str("\"european_learning_model_v3-3\"").expect("Failed to deserialize");
        assert_eq!(edc, CredentialType::EDC);
    }
}
