# Edubadges Metadata Extensions

This document describes the 17 metadata extensions of the Edubadges Metadata Model.
In the Open Badges standard OB2.x, an extension is described technically using, amongst other things, a JSON-LD context and a JSON Schema. This defines what the additional concept means, what it is called, what data type it has, and how it can be validated.

## Table of Contents

### Extensions for the Issuer
| # | Extension | Description |
|---|-----------|-------------|
| 1 | InstitutionCountryExtension | Country/Region of the issuer |
| 2 | InstitutionNameExtension | Name of the educational institution to which the issuer belongs |
| 3 | InstitutionIdentifierExtension | Unique identifier for the institution (BRIN number) |
| 4 | GradingTableExtension | URL to the institution's grading table |

### Extensions for the BadgeClass
| # | Extension | Description |
|---|-----------|-------------|
| 5 | LanguageExtension | Language in which the course is taught |
| 6 | ECTSExtension | Volume in ECTS credits/study points |
| 7 | StudyLoadExtension | Study load in hours (SBU) |
| 8 | TimeInvestmentExtension | Time required in hours |
| 9 | EQFExtension | European Qualifications Framework level |
| 10 | LearningOutcomeExtension | Description of the learning outcomes achieved |
| 11 | EducationProgramIdentifierExtension | Identification of the curriculum |
| 12 | ParticipationFormExtension | Format of participation: online, on-site, blended, etc. |
| 13 | AssesmentTypeExtension | Type of assessment/examination |
| 14 | SupervisionTypeExtension | Supervision and identity checks during examinations |
| 15 | QualityAssuranceExtension | Quality assurance in practice |
| 16 | IntegrationOptionsExtension | Whether the microcredential is standalone or stackable |

### Extensions for the Assertion
| # | Extension | Description |
|---|-----------|-------------|
| 17 | GradeAchievedExtension | Result/mark achieved at this particular award ceremony |

---

## Issuer Extensions

### 1. InstitutionCountryExtension

**Description:** Country/Region of the issuer. Under the EU proposal, every microcredential must contain the issuer's country code. This is described as "Country(ies)/Region(s) of the issuer" and is a mandatory field, but is not otherwise specified or explained. It is proposed that the 2-letter country code in accordance with ISO 3166-1 be used for this purpose.

**Example:**

```json
{
  "type": "Issuer",
  "id": "https://api.edubadges.nl/public/issuers/12345",
  "name": "Erasmus Universiteit Rotterdam",
  "extensions:InstitutionCountryExtension": {
    "@context": "https://api.edubadges.nl/extensions/InstitutionCountryExtension/context.json",
    "type": ["Extension", "extensions:InstitutionCountryExtension"],
    "CountryCode": "NL"
  }
}
```

| File | Path |
|------|------|
| context.json | [context.json](./InstitutionCountryExtension/context.json) |
| schema.json | [schema.json](./InstitutionCountryExtension/schema.json) |

### 2. InstitutionNameExtension

**Description:** Name of the educational institution to which the issuer belongs. As we do not regard an issuer as a separate entity but place it under an educational institution (Institution), we also need metadata elements to identify these institutions. The metadata field 'InstitutionNameExtension' is used to record the institution's name.

**Example:**

```json
{
  "type": "Issuer",
  "name": "Erasmus School of History, Culture and Communication",
  "extensions:InstitutionNameExtension": {
    "@context": "https://api.edubadges.nl/extensions/InstitutionNameExtension/context.json",
    "type": ["Extension", "extensions:InstitutionNameExtension"],
    "InstitutionName": "Erasmus Universiteit Rotterdam"
  }
}
```

| File | Path |
|------|------|
| context.json | [context.json](./InstitutionNameExtension/context.json) |
| schema.json | [schema.json](./InstitutionNameExtension/schema.json) |

### 3. InstitutionIdentifierExtension

**Description:** Unique identifier for the institution; in Edubadges, this is the BRIN number. A unique ID that identifies the institution. In Edubadges, we use the BRIN number for this purpose. The Basic Register of Institutions (BRIN) is a register maintained by the Dutch Ministry of Education, Culture and Science (OCW) / DUO, which lists all schools and related institutions.

**Example:** Institution code for Rotterdam University of Applied Sciences (BRIN): `22OJ`

| File | Path |
|------|------|
| context.json | [context.json](./InstitutionIdentifierExtension/context.json) |
| schema.json | [schema.json](./InstitutionIdentifierExtension/schema.json) |

### 4. GradingTableExtension

**Description:** URL to the institution's grading table. Link (URL) to the institution's grading table. Grading tables: higher education institutions explain the national grading system to ensure greater transparency and understanding. The explanation consists of grading tables that provide insight into different grading cultures across cohorts, programmes and faculties within an institution, as well as into grading cultures between institutions and countries.

**Example:** https://www.eur.nl/onderwijs/praktische-zaken/afstuderen/ects-grading-table

| File | Path |
|------|------|
| context.json | [context.json](./GradingTableExtension/context.json) |
| schema.json | [schema.json](./GradingTableExtension/schema.json) |

---

## BadgeClass Extensions

### 5. LanguageExtension

**Description:** Language in which the course is taught. This metadata field indicates the language in which the course was taught. The notation follows the BCP 47 / RFC 5646 standard.

**Example:** Language: `"nl_NL"`

| File | Path |
|------|------|
| context.json | [context.json](./LanguageExtension/context.json) |
| schema.json | [schema.json](./LanguageExtension/schema.json) |

### 6. ECTSExtension

**Description:** Volume in ECTS credits/study points. ECTS stands for 'European Credit Transfer and Accumulation System'. In the Netherlands, ECTS credits are expressed as study credits. Study credits indicate how much time you spend on a module or degree programme. 1 ECTS credit represents 28 hours of study. The concept of ECTS stems from an agreement reached by European ministers of education who wished to make higher education systems across different countries more comparable. In this way, they promote student mobility. These agreements, dating from 1998, are known as the Bologna Process.

**Minimum value:** 0.5 ECTS | **Maximum value:** 240 ECTS

**Example:** ECTS: 2.5

| File | Path |
|------|------|
| context.json | [context.json](./ECTSExtension/context.json) |
| schema.json | [schema.json](./ECTSExtension/schema.json) |

### 7. StudyLoadExtension

**Description:** Study load in hours (SBU). Study load hours. Instead of credits or ECTS, MBO institutions use the term 'study load hours' (SBU) to indicate how much time you spend on a subject or course.

**Example:** 140 study load hours

| File | Path |
|------|------|
| context.json | [context.json](./StudyLoadExtension/context.json) |
| schema.json | [schema.json](./StudyLoadExtension/schema.json) |

### 8. TimeInvestmentExtension

**Description:** Time required in hours. Whilst the ECTSExtension and StudyLoadExtension are used for Edubadges issued as part of a formal curriculum, this TimeInvestmentExtension metadata extension can be added to badge classes for extracurricular education to indicate the number of hours the learner must invest in order to obtain this Edubadge.

**Example:** TimeInvestment 36

| File | Path |
|------|------|
| context.json | [context.json](./TimeInvestmentExtension/context.json) |
| schema.json | [schema.json](./TimeInvestmentExtension/schema.json) |

### 9. EQFExtension

**Description:** Volume in ECTS credits/study points. EQF stands for the European Qualifications Framework. This provides information on the level of a course or programme in accordance with the International Standard Classification of Education (ISCED). In the Netherlands, this is expressed as the NLQF.

**Example:** NLQF 7

| File | Path |
|------|------|
| context.json | [context.json](./EQFExtension/context.json) |
| schema.json | [schema.json](./EQFExtension/schema.json) |

### 10. LearningOutcomeExtension

**Description:** Description of the learning outcomes achieved. Describes the learning outcome. Learning outcomes describe what a student knows, understands and is able to apply upon completion of a period of study. They are listed in the course catalogue and on the diploma supplement.

**Example:** "Upon completion of the course, the student should be able to explain the accounting concepts of revenue and transaction accounting."

| File | Path |
|------|------|
| context.json | [context.json](./LearningOutcomeExtension/context.json) |
| schema.json | [schema.json](./LearningOutcomeExtension/schema.json) |

### 11. EducationProgramIdentifierExtension

**Description:** Identification of the curriculum. An identification code that identifies the study programme: programme code. In the Netherlands, this is the ISAT code for a study programme. The Central Register of Higher Education Programmes (CROHO) contains information on past, current and future programmes.

**Example:** Erasmus University Rotterdam, Cultural Studies, ISAT/CROHO code: 56823

| File | Path |
|------|------|
| context.json | [context.json](./EducationProgramIdentifierExtension/context.json) |
| schema.json | [schema.json](./EducationProgramIdentifierExtension/schema.json) |

### 12. ParticipationFormExtension

**Description:** Format of participation: online, on-site, blended, etc. The format of participation in the learning module for which the Edubadge was issued. There may be more than one option.

**Options:** Blended, Online, On-site, Work Experience, Volunteering, Personalized Learning Activities, By Choice of Participant

| File | Path |
|------|------|
| context.json | [context.json](./ParticipationFormExtension/context.json) |
| schema.json | [schema.json](./ParticipationFormExtension/schema.json) |

### 13. AssesmentTypeExtension

**Description:** Type of assessment/examination. Indicates the type of assessment or evaluation that took place before the Edubadge was awarded. There may be more than one option.

**Options:** Professional project, Behavioural assessment, Personalised assessment, Development report/reflection report, Portfolio/portfolio assessment, Presentation/oral examination, Report/paper, Written examination

| File | Path |
|------|------|
| context.json | [context.json](./AssesmentTypeExtension/context.json) |
| schema.json | [schema.json](./AssesmentTypeExtension/schema.json) |

### 14. SupervisionTypeExtension

**Description:** Supervision and identity checks during examinations. Indicates whether the assessment/examination was supervised and whether the learner's identity was verified.

**Options:** unsupervisedWithNoIdentityVerification, unsupervisedWithIdentityVerification, supervisedWithNoIdentityVerification, supervisedWithIdentityVerification

| File | Path |
|------|------|
| context.json | [context.json](./SupervisionTypeExtension/context.json) |
| schema.json | [schema.json](./SupervisionTypeExtension/schema.json) |

### 15. QualityAssuranceExtension

**Description:** Quality assurance in practice. Specifies the quality framework that underpins the issuance of the Edubadge/Microcredential. To ensure the quality of microcredentials, vocational education (MBO), higher professional education (HBO) and university education (WO) have committed, through their sector associations, to shared quality frameworks. Microcredentials issued within this framework are therefore nationally recognisable to institutions and employers, and mutually recognised between institutions.

**Example:** Quality framework for higher vocational education (HBO) and university (WO) microcredentials

| File | Path |
|------|------|
| context.json | [context.json](./QualityAssuranceExtension/context.json) |
| schema.json | [schema.json](./QualityAssuranceExtension/schema.json) |

### 16. IntegrationOptionsExtension

**Description:** Whether the microcredential is standalone or stackable. The IntegrationOptionsExtension specifies, for a BadgeClass, whether the relevant Edubadge or microcredential can be combined or stacked with other Edubadges or microcredentials. There are essentially two possibilities:

- **Standalone / independent microcredential** — the microcredential stands on its own and does not need to form part of a larger learning or credential pathway.
- **Integrated / stackable towards another credential** — the microcredential can be stacked or combined and contribute towards another or larger credential.

| File | Path |
|------|------|
| context.json | [context.json](./IntegrationOptionsExtension/context.json) |
| schema.json | [schema.json](./IntegrationOptionsExtension/schema.json) |

---

## Assertion Extensions

### 17. GradeAchievedExtension

**Description:** Result/mark achieved at this particular award ceremony. The GradeAchievedExtension indicates the result or assessment achieved by an individual recipient for the relevant edubadge/microcredential. The main difference compared with many other edubadge extensions is that GradeAchievedExtension is associated with the Assertion, rather than the BadgeClass.

**Example:** Assertion for student A: GradeAchieved = 8

| File | Path |
|------|------|
| context.json | [context.json](./GradeAchievedExtension/context.json) |
| schema.json | [schema.json](./GradeAchievedExtension/schema.json) |

---

## Decision Log

Traceable decisions made during extraction and refinement of the 17 extensions from the PDF source document. Each entry records the question raised, the answer given, and the resulting consequence.

### D-001 — Schema Draft Version

| Field | Value |
|-------|-------|
| **Question** | Extensions used three different JSON Schema drafts: `draft-04`, `draft/2020-12`, and some had no `$schema` at all. Should they be unified? |
| **Answer** | Yes — unified to a single version across all 17 extensions. |
| **Consequence** | Every schema.json now declares `"$schema": "https://json-schema.org/draft/2020-12/schema"`. This aligns with how `exclusiveMinimum`/`exclusiveMaximum` are now numeric (not boolean). Consuming code must support draft-2020-12. |

### D-002 — `exclusiveMinimum` Semantics

| Field | Value |
|-------|-------|
| **Question** | Why did some schemas use `exclusiveMinimum: 0` as a number vs. a boolean? |
| **Answer** | The original PDF had mixed conventions. After unifying to draft-2020-12, `TimeInvestmentExtension` correctly uses `exclusiveMinimum: 0` (numeric form). No other extension needs this constraint. |
| **Consequence** | Only `TimeInvestmentExtension` uses `exclusiveMinimum: 0`. All other numeric constraints (`minimum`, `maximum`) use the same numeric form consistently. |

### D-003 — `LearningOutcomeExtension` Duplicate Context Key

| Field | Value |
|-------|-------|
| **Question** | The source document lists two `learningOutcomes` keys in the `@context` — one with `@id`/`@container`, one with `description`. They collide; the second overwrites the first. |
| **Answer** | This was documented in the PDF but never actually implemented. It is a specification error. |
| **Consequence** | The `@context` was rewritten to merge both concepts: `learningOutcomes` maps to `@id`/`@container`, and `description` maps to `dc:description`. Added a missing `obi:validation` block. |

### D-004 — `GradingTableExtension` Context Key

| Field | Value |
|-------|-------|
| **Question** | The context mapped the extension type (`extensions:GradingTableExtension`) as the predicate for `GradingTableURL`. Should the context key match the schema property name? |
| **Answer** | Yes — use the schema property name `GradingTableURL` as the context key. |
| **Consequence** | `context.json` maps `"GradingTableURL": "extensions:GradingTableExtension"`, consistent with how other extensions map property names to extension predicates. |

### D-005 — `EducationProgramIdentifier` Type

| Field | Value |
|-------|-------|
| **Question** | The PDF example shows `"EducationProgramIdentifier": 56823` (number), but the schema says `string`. Which is correct? |
| **Answer** | String — identifiers are not calculated with, so there is no need for a numeric type. |
| **Consequence** | Schema remains `type: "string"` (it already was). The PDF example is documentation-only and was not changed. |

### D-006 — Optional Properties in `QualityAssuranceExtension`

| Field | Value |
|-------|-------|
| **Question** | `QualityAssuranceUrl` and `QualityAssuranceDescription` are optional (not in `required`). Do optional properties still need to be listed in `properties`? |
| **Answer** | Yes — if they are optional, they should remain in `properties` but not in `required`. |
| **Consequence** | Schema has `required: ["QualityAssuranceName"]` only. `QualityAssuranceUrl` and `QualityAssuranceDescription` are documented in `properties` as optional. `additionalProperties: false` prevents unknown fields. |

### D-007 — Enum Value Conventions

| Field | Value |
|-------|-------|
| **Question** | Enum values used mixed conventions: `camelCase` (`workExperience`), `snake_case-ish` (`unsupervisedWithNoIdentityVerification`), and raw labels (`Tentamen`). |
| **Answer** | Unify to camelCase across all enums. |
| **Consequence** | All enum values use camelCase: `ParticipationFormExtension` (`workExperience`, `personalizedLearningActivities`), `AssesmentTypeExtension` (`recognitionOfPriorLearning`, `personalizedAssessment`), `SupervisionTypeExtension` (`unsupervisedWithNoIdentityVerification`, `supervisedWithIdentityVerification`). |

### D-008 — `obi:validation` Schema URLs

| Field | Value |
|-------|-------|
| **Question** | `obi:validation` blocks referenced three different hostnames: `api.edubadges.nl`, `w3id.org/openbadges/extensions`, and `example.org`. |
| **Answer** | Temporarily unify all to `api.edubadges.nl` — these need replacing later anyway. |
| **Consequence** | Every `obi:validationSchema` now resolves to `https://api.edubadges.nl/extensions/<ExtensionName>/schema.json`. |

### D-009 — `LearningOutcomeExtension` Missing Validation Block

| Field | Value |
|-------|-------|
| **Question** | `LearningOutcomeExtension` had no `obi:validation` block in its context.json, unlike all other 16 extensions. |
| **Answer** | Add the missing validation block. |
| **Consequence** | `context.json` now includes `"obi:validation"` with `obi:validatesType: "extensions:LearningOutcomeExtension"` and the corresponding schema URL. |

### D-010 — `GradeAchievedExtension` Missing `additionalProperties: false`

| Field | Value |
|-------|-------|
| **Question** | `GradeAchievedExtension` was the only extension without `additionalProperties: false`. Is this intentional? |
| **Answer** | No — add it for consistency. |
| **Consequence** | All 17 schemas now close with `"additionalProperties": false`. |

### D-011 — `TimeInvestmentExtension` Draft Compatibility

| Field | Value |
|-------|-------|
| **Question** | `TimeInvestmentExtension` used `exclusiveMinimum: 0` (numeric) on a draft-04 schema. Draft-04 expects `exclusiveMinimum` as a boolean alongside `minimum`. |
| **Answer** | Since D-001 unified to draft-2020-12, the numeric form is correct. |
| **Consequence** | `exclusiveMinimum: 0` is now correctly paired with `"$schema": "https://json-schema.org/draft/2020-12/schema"`. No change to the numeric value itself. |

---

**Summary of changes:** 11 decisions applied across 17 extensions. All schemas now use draft-2020-12, all validation URLs point to `api.edubadges.nl`, all enums use camelCase, and all 17 schemas include `additionalProperties: false`. |