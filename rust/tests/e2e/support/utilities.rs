/// Utility functions for e2e tests.
use std::path::PathBuf;

const _TESTS_E2E_DIR: &str = env!("CARGO_MANIFEST_DIR");

/// Load a JSON schema from `tests/e2e/schemas/<schema_name>.json`.
pub fn load_schema(schema_name: &str) -> serde_json::Value {
    let path = PathBuf::from(format!(
        "{_TESTS_E2E_DIR}/tests/e2e/schemas/{schema_name}.json"
    ));
    let content = std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("Failed to read schema {path:?}: {e}"));
    serde_json::from_str(&content).expect("Schema is not valid JSON")
}

/// Validate `data` against a JSON schema from the schemas directory.
pub fn assert_schema(data: &serde_json::Value, schema_name: &str) {
    let schema = load_schema(schema_name);
    let compiled = jsonschema::validator_for(&schema).expect("Schema failed to compile");
    compiled
        .validate(data)
        .unwrap_or_else(|e| panic!("Data does not match schema {schema_name}: {e}"));
}
