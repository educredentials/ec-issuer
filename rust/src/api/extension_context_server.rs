/// Serve JSON-LD extension contexts for credential validation.
///
/// This module owns all trust-boundary logic for serving extension files:
/// name-pattern checking, `realpath` containment checks, `${BASE_URL}`
/// substitution, and disk reads.  No environment variable reads — all
/// configuration is injected from `Config` at application bootstrap.
use std::path::PathBuf;

use regex::Regex;
use tracing::debug;

/// Serve JSON-LD extension contexts from a filesystem directory.
///
/// Only files under `extensions_dir` are served.  The `${BASE_URL}`
/// placeholder in context files is replaced with `base_url` so that
/// generated credentials carry the correct absolute URLs for their
/// validation schemas.
#[derive(Clone)]
pub struct ExtensionContextServer {
    base_url: String,
    extensions_dir: PathBuf,
    filename_pattern: Regex,
}

impl ExtensionContextServer {
    /// Create a new extension context server.
    ///
    /// # Arguments
    ///
    /// * `base_url` - The public base URL of this issuer.
    /// * `extensions_dir` - Path to the directory containing extension files.
    pub fn new(base_url: &str, extensions_dir: &str) -> Self {
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            extensions_dir: PathBuf::from(extensions_dir),
            filename_pattern: Regex::new(
                r"^([a-zA-Z0-9]+/)?[a-zA-Z0-9_-]+/(context|schema)\.json$",
            )
            .expect("filename_pattern is valid regex"),
        }
    }

    /// Serve an extension context or schema file.
    ///
    /// # Arguments
    ///
    /// * `filename` - The path component after `/static/extensions/`,
    ///   e.g. `v1/EQFExtension/context.json`.
    ///
    /// # Returns
    ///
    /// A tuple of `(content, status_code, content_type)`.
    /// On failure the status code is 404 and content is a short message.
    pub fn serve(&self, filename: &str) -> (String, u16, Option<String>) {
        if !self.filename_pattern.is_match(filename) {
            debug!(filename, "Rejected by filename pattern");
            return ("not found".to_string(), 404, None);
        }

        let path = self.extensions_dir.join(filename);
        let resolved = match path.canonicalize() {
            Ok(p) => p,
            Err(e) => {
                debug!(filename, error = %e, "Failed to canonicalize path");
                return ("not found".to_string(), 404, None);
            }
        };

        let ext_dir_resolved = match self.extensions_dir.canonicalize() {
            Ok(p) => p,
            Err(e) => {
                debug!(error = %e, "Failed to canonicalize extensions_dir");
                return ("not found".to_string(), 404, None);
            }
        };

        if !resolved.is_file() {
            debug!(path = ?resolved, "Path is not a file");
            return ("not found".to_string(), 404, None);
        }

        if !resolved.starts_with(&ext_dir_resolved) {
            debug!(path = ?resolved, dir = ?ext_dir_resolved, "Path escapes extensions directory");
            return ("not found".to_string(), 404, None);
        }

        match std::fs::read_to_string(&resolved) {
            Ok(mut content) => {
                content = content.replace("${BASE_URL}", &self.base_url);
                debug!(filename, "Served extension file");
                (content, 200, Some("application/ld+json".to_string()))
            }
            Err(e) => {
                debug!(filename, error = %e, "Failed to read file");
                ("not found".to_string(), 404, None)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn setup_test_dir() -> (String, String) {
        let dir = std::env::temp_dir().join("ec_issuer_test_extensions");
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).expect("Failed to create test dir");

        let v1_dir = dir.join("v1/EQFExtension");
        fs::create_dir_all(&v1_dir).expect("Failed to create test subdirs");

        fs::write(
            v1_dir.join("context.json"),
            r#"{"@context": ["${BASE_URL}/test"]}"#,
        )
        .expect("Failed to write test file");

        let base_url = "http://localhost:8000".to_string();
        (base_url, dir.to_string_lossy().to_string())
    }

    #[test]
    fn test_serve_valid_file() {
        let (base_url, dir) = setup_test_dir();
        let server = ExtensionContextServer::new(&base_url, &dir);

        let (content, status, _ct) = server.serve("v1/EQFExtension/context.json");
        assert_eq!(status, 200);
        assert!(content.contains(&base_url));
    }

    #[test]
    fn test_serve_nonexistent_file() {
        let (base_url, dir) = setup_test_dir();
        let server = ExtensionContextServer::new(&base_url, &dir);

        let (content, status, _ct) = server.serve("v1/NonExistent/context.json");
        assert_eq!(status, 404);
        assert_eq!(content, "not found");
    }

    #[test]
    fn test_serve_path_traversal() {
        let (base_url, dir) = setup_test_dir();
        let server = ExtensionContextServer::new(&base_url, &dir);

        let (content, status, _ct) = server.serve("../../etc/passwd");
        assert_eq!(status, 404);
        assert_eq!(content, "not found");
    }

    #[test]
    fn test_serve_invalid_filename_pattern() {
        let (base_url, dir) = setup_test_dir();
        let server = ExtensionContextServer::new(&base_url, &dir);

        let (content, status, _ct) = server.serve("invalid_filename.txt");
        assert_eq!(status, 404);
        assert_eq!(content, "not found");
    }
}
