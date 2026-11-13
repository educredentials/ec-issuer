/// Domain models for awards (OB3 `AchievementCredential`).
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Assessment type per Open Badges `AssessmentTypeExtension`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum AssessmentTypeEnum {
    Testing,
    #[serde(rename = "applicationOfSkill")]
    ApplicationOfSkill,
    Portfolio,
    #[serde(rename = "recognitionOfPriorLearning")]
    RecognitionOfPriorLearning,
    #[serde(rename = "personalizedAssessment")]
    PersonalizedAssessment,
    #[serde(rename = "byChoiceOfParticipant")]
    ByChoiceOfParticipant,
}

impl AssessmentTypeEnum {
    /// Attempt to parse an arbitrary string as an `AssessmentTypeEnum`.
    ///
    /// Returns `None` when the string does not match any known value.
    #[must_use]
    #[allow(clippy::should_implement_trait)]
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "testing" => Some(Self::Testing),
            "applicationOfSkill" => Some(Self::ApplicationOfSkill),
            "portfolio" => Some(Self::Portfolio),
            "recognitionOfPriorLearning" => Some(Self::RecognitionOfPriorLearning),
            "personalizedAssessment" => Some(Self::PersonalizedAssessment),
            "byChoiceOfParticipant" => Some(Self::ByChoiceOfParticipant),
            _ => None,
        }
    }
}

/// Criteria for earning an achievement.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Criteria {
    pub narrative: String,
}

/// An achievement within an award.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Achievement {
    pub id: String,
    pub r#type: Vec<String>,
    pub criteria: Criteria,
    pub description: String,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image: Option<HashMap<String, String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub in_language: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ects: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub eqf: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub learning_outcome: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub education_program_identifier: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub form_of_participation: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub assessment_type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub supervision_type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub time_investment: Option<f64>,
}

/// The subject of an `AchievementCredential`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AchievementSubject {
    pub id: String,
    pub r#type: Vec<String>,
    pub achievement: Achievement,
    #[serde(default)]
    pub identifier: Vec<IdentityObject>,
}

/// Address for parentOrg.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Address {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub address_country_code: Option<String>,
    #[serde(default = "default_address_type")]
    pub r#type: Vec<String>,
}

fn default_address_type() -> Vec<String> {
    vec!["Address".to_string()]
}

/// Entry in parentOrg.otherIdentifier.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentifierEntry {
    pub identifier: String,
    #[serde(rename = "identifierType")]
    pub identifier_type: String,
    #[serde(
        skip_serializing_if = "should_skip_type",
        default = "default_identifier_type"
    )]
    pub r#type: String,
}

fn should_skip_type(s: &String) -> bool {
    s == "IdentifierEntry"
}

fn default_identifier_type() -> String {
    "IdentifierEntry".to_string()
}

/// Parent organization of the issuer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParentOrg {
    pub id: String,
    pub name: String,
    #[serde(default = "default_profile_type")]
    pub r#type: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub address: Option<Address>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub other_identifier: Vec<IdentifierEntry>,
}

fn default_profile_type() -> Vec<String> {
    vec!["Profile".to_string()]
}

/// The issuer of an `AchievementCredential`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Issuer {
    pub id: String,
    pub name: String,
    #[serde(default = "default_profile_type")]
    pub r#type: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub parent_org: Option<ParentOrg>,
}

/// An identifier for the recipient of an achievement (OB3 spec).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentityObject {
    pub r#type: String,
    #[serde(rename = "identityHash")]
    pub identity_hash: String,
    #[serde(rename = "identityType")]
    pub identity_type: String,
    pub hashed: bool,
}

/// Token Status List credential status entry.
///
/// Managed by the vc-service: it assigns the index, hosts the compressed
/// bitstring at the URI, and flips bits on revocation / suspension.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CredentialStatus {
    pub id: String,
    pub idx: usize,
    pub uri: String,
    #[serde(
        skip_serializing_if = "should_skip_type",
        default = "default_status_type"
    )]
    pub r#type: String,
}

fn default_status_type() -> String {
    "statuslist+jwt".to_string()
}

impl Default for CredentialStatus {
    fn default() -> Self {
        Self {
            id: String::new(),
            idx: 0,
            uri: String::new(),
            r#type: default_status_type(),
        }
    }
}

/// Return the default OB3 credential schema.
#[must_use]
pub fn ob3_default_schema() -> Vec<HashMap<String, String>> {
    let mut map = HashMap::new();
    map.insert(
        "id".to_string(),
        "https://purl.imsglobal.org/spec/ob/v3p0/schema/json/ob_v3p0_achievementcredential_schema.json"
            .to_string(),
    );
    map.insert(
        "type".to_string(),
        "1EdTechJsonSchemaValidator2019".to_string(),
    );
    vec![map]
}

/// Open Badges 3.0 `AchievementCredential` (unsigned).
///
/// Fields beyond the OB3 core spec represent VCDM 2.0 extension properties.
/// They are serialized to JSON as top-level credential keys, not wrapped
/// in an `extensions` array, and are validated against the SSI-agent
/// template schema. `credential_context` carries the `@context` URLs
/// needed by the SSI agent for signing. `credentialStatus` carries the
/// Token Status List status entry managed by the vc-service.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OB3Award {
    pub id: String,
    pub r#type: Vec<String>,
    pub name: String,
    pub issuer: Issuer,
    #[serde(rename = "validFrom")]
    pub valid_from: String,
    #[serde(rename = "credentialSubject")]
    pub credential_subject: AchievementSubject,
    #[serde(default = "ob3_default_schema", rename = "credentialSchema")]
    pub credential_schema: Vec<HashMap<String, String>>,
    // --- OB3 / VCDM 2.0 extension properties ---
    #[serde(rename = "validUntil", skip_serializing_if = "Option::is_none")]
    pub valid_until: Option<String>,
    /// Source `entity_id` from Badgr (e.g. assertion URL), used by the adapter
    /// to derive credentialStatus idx.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<String>,
    /// Context for SSI-agent signing.
    #[serde(skip_serializing_if = "Option::is_none", rename = "@context")]
    pub credential_context: Option<Vec<CredentialContextItem>>,
    /// Token Status List entry managed by the vc-service.
    #[serde(skip_serializing_if = "Option::is_none", rename = "credentialStatus")]
    pub credential_status: Option<CredentialStatus>,
}

/// A single item in the `@context` array (URL string or inline term definitions).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum CredentialContextItem {
    Url(String),
    Inline(HashMap<String, String>),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_assessment_type_enum() {
        assert_eq!(
            AssessmentTypeEnum::from_str("testing"),
            Some(AssessmentTypeEnum::Testing),
        );
        assert_eq!(
            AssessmentTypeEnum::from_str("applicationOfSkill"),
            Some(AssessmentTypeEnum::ApplicationOfSkill),
        );
        assert_eq!(
            AssessmentTypeEnum::from_str("portfolio"),
            Some(AssessmentTypeEnum::Portfolio),
        );
        assert_eq!(
            AssessmentTypeEnum::from_str("recognitionOfPriorLearning"),
            Some(AssessmentTypeEnum::RecognitionOfPriorLearning),
        );
        assert_eq!(
            AssessmentTypeEnum::from_str("personalizedAssessment"),
            Some(AssessmentTypeEnum::PersonalizedAssessment),
        );
        assert_eq!(
            AssessmentTypeEnum::from_str("byChoiceOfParticipant"),
            Some(AssessmentTypeEnum::ByChoiceOfParticipant),
        );
    }

    #[test]
    fn test_assessment_type_enum_unknown() {
        assert_eq!(AssessmentTypeEnum::from_str("unknown_type"), None);
    }

    #[test]
    fn test_criteria_default() {
        let criteria = Criteria::default();
        assert_eq!(criteria.narrative, "");
    }

    #[test]
    fn test_credential_status_default() {
        let status = CredentialStatus::default();
        assert_eq!(status.r#type, "statuslist+jwt");
        assert_eq!(status.idx, 0);
    }

    #[test]
    fn test_ob3_award_serialization() {
        let json = r#"{
            "id": "credential-1",
            "type": ["VerifiableCredential", "AchievementCredential"],
            "name": "Test Credential",
            "issuer": {"id": "issuer-1", "name": "Test Issuer", "type": ["Profile"]},
            "validFrom": "2024-01-01T00:00:00Z",
            "credentialSubject": {
                "id": "subject-1",
                "type": ["AchievementSubject"],
                "achievement": {
                    "id": "credential-1",
                    "type": ["Achievement"],
                    "criteria": {"narrative": "Test criteria"},
                    "description": "Test description",
                    "name": "Test Credential"
                }
            }
        }"#;

        let award: OB3Award = serde_json::from_str(json).expect("Failed to deserialize OB3Award");
        assert_eq!(award.id, "credential-1");
        assert_eq!(award.name, "Test Credential");
        assert_eq!(award.valid_from, "2024-01-01T00:00:00Z");
    }

    #[test]
    fn test_ob3_default_schema() {
        let schema = ob3_default_schema();
        assert_eq!(schema.len(), 1);
        assert!(schema[0].contains_key("id"));
        assert!(schema[0].contains_key("type"));
    }
}
