/// Utility functions for e2e tests.

use std::path::PathBuf;

pub fn jsonpath_value(data: &serde_json::Value, expression: &str) -> serde_json::Value {
    // Simplified: just return the data for now.
    // Full JSONPath support would add the jsonpath library as a dev dependency.
    data.clone()
}
