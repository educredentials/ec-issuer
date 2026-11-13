//! Token-based access control adapter.
//!
//! Blocks anonymous (empty-token) requests. Real authorization is delegated to
//! the downstream awards service.

/// Access control port trait.
pub trait AccessControlPort {
    /// Check whether the caller may perform an action on a resource.
    fn may_import(
        &self,
        bearer_token: &str,
        resource_id: &str,
        resource_type: &str,
        permission: &str,
    ) -> bool;
}

/// Adapter that grants permission only when a non-empty bearer token is present.
pub struct TokenAccessControlAdapter;

impl AccessControlPort for TokenAccessControlAdapter {
    /// Grant permission when `bearer_token` is non-empty.
    ///
    /// # Arguments
    ///
    /// * `bearer_token` - The caller's bearer token.
    /// * `resource_id` - The resource identifier (unused).
    /// * `resource_type` - The resource type (unused).
    /// * `permission` - The permission being checked (unused).
    ///
    /// # Returns
    ///
    /// `true` when `bearer_token` is non-empty, `false` otherwise.
    fn may_import(
        &self,
        bearer_token: &str,
        _resource_id: &str,
        _resource_type: &str,
        _permission: &str,
    ) -> bool {
        !bearer_token.is_empty()
    }
}
