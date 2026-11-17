use crate::awards::badgr_dtos::{BadgeclassExtensions, BadgrBadgeclass};
use crate::awards::models::CredentialContextItem;
use crate::offers::models::CredentialType;

/// Extract extension field values from a Badgr badgeclass into a structured DTO.
///
/// If the badgeclass is `None`, returns the default (all fields `None`).
pub(super) fn _extract_extension_values(
    badgeclass: Option<&BadgrBadgeclass>,
) -> BadgeclassExtensions {
    let Some(bc) = badgeclass else {
        return BadgeclassExtensions::default();
    };

    BadgeclassExtensions {
        in_language: bc.language.clone(),
        ects: bc
            .ects
            .as_ref()
            .and_then(|v| v.as_str().map(std::string::ToString::to_string)),
        eqf: bc
            .eqf
            .as_ref()
            .and_then(|v| v.as_str().map(std::string::ToString::to_string)),
        learning_outcome: bc.learning_outcome.clone(),
        education_program_identifier: bc.education_program_identifier.as_ref().and_then(|v| {
            v.as_array().map(|arr| {
                arr.iter()
                    .filter_map(|val| val.as_str().map(String::from))
                    .collect()
            })
        }),
        time_investment: bc.time_investment.map(|t| t.to_string()),
        supervision_type: bc.supervision_type.clone(),
        assessment_type: bc.assessment_type.clone(),
        participation: bc.participation.clone(),
    }
}

/// Build a list of extension context URLs with non-null field values,
/// filtered by credential type.
///
/// For OB3, all OB3 extension fields apply.
/// ELM/EDC extensions are not yet wired — they will be filtered out here
/// once the ELM extension context list is known.
pub(super) fn _credential_context_urls(
    issuer_base_url: &str,
    extensions_url_prefix: &str,
    ext_vals: &BadgeclassExtensions,
    credential_type: Option<CredentialType>,
) -> Option<Vec<CredentialContextItem>> {
    let _ = credential_type;
    let ext_map: Vec<(&str, bool)> = vec![
        (
            "LearningOutcomeExtension/context.json",
            ext_vals.learning_outcome.is_some(),
        ),
        ("ECTSExtension/context.json", ext_vals.ects.is_some()),
        ("EQFExtension/context.json", ext_vals.eqf.is_some()),
        (
            "TimeInvestmentExtension/context.json",
            ext_vals.time_investment.is_some(),
        ),
        (
            "SupervisionTypeExtension/context.json",
            ext_vals.supervision_type.is_some(),
        ),
        (
            "EducationProgramIdentifierExtension/context.json",
            ext_vals.education_program_identifier.is_some(),
        ),
    ];

    let urls: Vec<String> = ext_map
        .into_iter()
        .filter_map(|(filename, present)| {
            if present {
                Some(format!(
                    "{issuer_base_url}{extensions_url_prefix}/{filename}"
                ))
            } else {
                None
            }
        })
        .collect();

    if urls.is_empty() {
        None
    } else {
        Some(urls.into_iter().map(CredentialContextItem::Url).collect())
    }
}
