/// Badgr DTOs and mapping to OB3 award domain model.
///
/// Error raised when a Badgr award response cannot be mapped to an OB3 award.
#[derive(Debug, thiserror::Error)]
#[error("badgr mapping error: {0}")]
pub struct AwardMappingError(pub String);

/// Faculty within issuer.
#[allow(dead_code)]
#[derive(Debug, Default, Clone, serde::Deserialize)]
pub struct BadgrFaculty {
    pub(crate) entity_id: Option<String>,
    pub(crate) name_dutch: Option<String>,
    pub(crate) name_english: Option<String>,
    pub(crate) image_dutch: Option<String>,
    pub(crate) image_english: Option<String>,
    pub(crate) on_behalf_of: Option<serde_json::Value>,
    pub(crate) on_behalf_of_display_name: Option<String>,
    pub(crate) on_behalf_of_url: Option<String>,
    pub(crate) institution: Option<BadgrInstitution>,
}

/// Institution within faculty.
#[allow(dead_code)]
#[derive(Debug, Default, Clone, serde::Deserialize)]
pub struct BadgrInstitution {
    pub(crate) entity_id: Option<String>,
    pub(crate) name_dutch: Option<String>,
    pub(crate) name_english: Option<String>,
    pub(crate) image_dutch: Option<String>,
    pub(crate) image_english: Option<String>,
    pub(crate) identifier: Option<String>,
    pub(crate) alternative_identifier: Option<String>,
    pub(crate) country_code: Option<String>,
    pub(crate) brin: Option<String>,
}

/// Issuer within badgeclass.
#[allow(dead_code)]
#[derive(Debug, Default, serde::Deserialize)]
pub struct BadgrIssuer {
    pub(crate) entity_id: Option<String>,
    pub(crate) name_dutch: Option<String>,
    pub(crate) name_english: Option<String>,
    pub(crate) faculty: Option<BadgrFaculty>,
    pub(crate) r#type: Option<String>,
}

/// Criteria inside badgeclass.
#[derive(Debug, Default, serde::Deserialize)]
pub struct BadgrCriteria {
    pub(crate) narrative: Option<String>,
}

/// Badgeclass extensions extracted from flat fields.
#[derive(Debug, Default, serde::Deserialize)]
pub struct BadgeclassExtensions {
    pub(crate) in_language: Option<String>,
    pub(crate) ects: Option<String>,
    pub(crate) eqf: Option<String>,
    pub(crate) learning_outcome: Option<String>,
    pub(crate) education_program_identifier: Option<Vec<String>>,
    pub(crate) time_investment: Option<String>,
    pub(crate) supervision_type: Option<String>,
    pub(crate) assessment_type: Option<Vec<String>>,
    pub(crate) participation: Option<Vec<String>>,
}

/// Badgeclass.
#[allow(dead_code)]
#[derive(Debug, Default, serde::Deserialize)]
pub struct BadgrBadgeclass {
    pub(crate) name: String,
    pub(crate) entity_id: Option<String>,
    pub(crate) description: Option<String>,
    pub(crate) criteria_text: Option<String>,
    pub(crate) image: Option<String>,
    pub(crate) criteria: Option<BadgrCriteria>,
    pub(crate) issuer: Option<BadgrIssuer>,
    pub(crate) eqf: Option<serde_json::Value>,
    pub(crate) ects: Option<serde_json::Value>,
    pub(crate) language: Option<String>,
    pub(crate) learning_outcome: Option<String>,
    pub(crate) time_investment: Option<f64>,
    pub(crate) education_program_identifier: Option<serde_json::Value>,
    pub(crate) participation: Option<Vec<String>>,
    pub(crate) assessment_type: Option<Vec<String>>,
    pub(crate) assessment_id_verified: Option<bool>,
    pub(crate) assessment_supervised: Option<bool>,
    pub(crate) supervision_type: Option<String>,
}

/// Badgr awards API response.
#[allow(dead_code)]
#[derive(Debug, Default, serde::Deserialize)]
pub struct BadgrAwardResponse {
    pub(crate) entity_id: Option<String>,
    pub(crate) name: Option<String>,
    pub(crate) issued_on: Option<String>,
    pub(crate) image: Option<String>,
    pub(crate) badgeclass: Option<BadgrBadgeclass>,
    pub(crate) given_name: Option<String>,
    pub(crate) family_name: Option<String>,
    pub(crate) email: Option<String>,
    pub(crate) expires_at: Option<String>,
    pub(crate) language: Option<String>,
    pub(crate) ects: Option<serde_json::Value>,
    pub(crate) eqf: Option<serde_json::Value>,
    pub(crate) participation: Option<Vec<String>>,
    pub(crate) assessment_type: Option<Vec<String>>,
    pub(crate) assessment_id_verified: Option<bool>,
    pub(crate) assessment_supervised: Option<bool>,
    pub(crate) learning_outcome: Option<String>,
    pub(crate) education_program_identifier: Option<serde_json::Value>,
    pub(crate) time_investment: Option<f64>,
}

impl BadgrAwardResponse {
    pub(crate) fn from_json(json: &serde_json::Value) -> Result<Self, serde_json::Error> {
        serde_json::from_value(json.clone())
    }
}
