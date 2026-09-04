# Delegate OB3 → ELM mapping to the credential-converter service

| | |
| --- | --- |
| Status | proposed |
| Date | 2026-09-04 |
| Deciders | Engineering Team |
| Consulted | - |
| Informed | All stakeholders |

## Context and Problem Statement

The ec-issuer must issue **European Digital Credential (EDC)** credentials in addition to Open Badges v3. An EDC credential is written in the **European Learner Model (ELM)** standard, which has a completely different schema, field names, and mandatory/optional constraints from OBv3.

The mapping is not a simple field rename — it is a bidirectional data-transformation engine with:

- Nested object reconstruction (e.g. `badgeclass.description → learning_achievement.description`, `badgeclass.issuer.name → awarding_body.name`)
- Field transformations: lower-casing, upper-casing, slicing strings and arrays, taking specific indices, regex substitutions, one-to-many and many-to-one expansions
- JSON Schema logic: resolving `allOf`, `anyOf`, `oneOf`, `not` logical constructs for mandatory/optional field selection
- Language-aware mapping with `PreferredLanguages` parameters
- Custom mapping file support for domain-specific overrides
- Two full JSON Schema profiles to maintain

Writing this mapping in Python would mean thousands of lines of domain logic, constant maintenance as OB3 and ELM schemas evolve, and a deep dependency on both standards' documentation.

The **credential-converter** is a Rust-based service that provides exactly this mapping. It is maintained by ourselves, runs in our infrastructure as a peer service, and exposes a simple JSON-over-HTTP API.

## Decision Drivers

- **Complexity is unacceptable in-process.** The mapping engine involves JSON Schema resolution, field transformations, nested object reconstruction, and language parameters. This is non-trivial logic that has been iteratively refined in the Rust codebase.
- **The converter is already in our infrastructure.** The `credential-converter` image runs in our podman compose environment, alongside ssi-agent and ec-issuer.
- **The converter is maintained by our team.** Impierce maintains the converter, so bug fixes and schema updates stay in sync with our needs.
- **Single source of truth.** Both the TUI and the headless API use the same conversion engine, guaranteeing consistency.
- **Performance is handled.** The Rust implementation handles the heavy transformation work efficiently.

## Considered Options

- **Option A — Call the credential-converter service** (chosen): Add an external HTTP call from ec-issuer to the converter. The converter handles the full mapping; ec-issuer only passes the OB3 credential dict and receives the ELM dict.
- **Option B — Implement the mapping in Python**: Write Python dataclasses and transformation logic mirroring the converter's behavior.
- **Option C — Generate mapping logic from JSON Schema**: Attempt to derive a Python transformer from the OB3 and ELM JSON Schema files automatically.

## Decision Outcome

Chosen option: **"Option A — Call the credential-converter service"**, because:

- The mapping complexity (nested objects, field transformations, JSON Schema logic, language parameters) is a substantial engineering investment best handled by the existing Rust service.
- The converter is already running in our infrastructure and maintained by our team.
- ec-issuer remains focused on its core responsibility: orchestrating the credential-offer lifecycle.
- The HTTP call is fast (typically <50ms on local network) and adds negligible latency to the offer creation flow.

### Consequences

- **Good**: ec-issuer stays lean — one `convert()` call, no mapping logic, no schema dependency.
- **Good**: The converter is the single source of truth for OB3→ELM mapping; changes happen in one place.
- **Good**: Performance is handled by the Rust implementation.
- **Neutral**: Adds one HTTP hop to the EDC path (converter → vc-service). The OB3 path is unaffected.
- **Neutral**: ec-issuer now depends on the converter service being available and healthy.
- **Bad**: The EDC path has an extra failure point (converter network errors, 4xx/5xx responses). Mitigated by `CredentialConverterClientError` wrapping all failures and the converter's health check.
- **Bad**: The converter must be started separately in compose. Already handled via `depends_on`.

### Flow comparison

| Step | OB3 path | EDC path (chosen) |
|------|----------|-------------------|
| 1 | `get_ob3(award_id, token)` | `get_ob3(award_id, token)` |
| 2 | `create_ob3(offer_id, award)` | `asdict(award)` |
| | | `convert(raw_ob3)` → `credential_convetor` |
| | | `create_edc(offer_id, converted)` |
| 3 | store + return | store + return |

Both paths share steps 1 and 3. The EDC path inserts one HTTP call between steps 1 and 2.
