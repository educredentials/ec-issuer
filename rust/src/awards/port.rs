/// Awards client port trait.
use super::client::HttpAwardsClient;
use super::models::OB3Award;

/// Port: interface for fetching awards from the external awards service.
pub trait AwardsClientPort {
    /// Fetch and convert an award to an OB3 `AchievementCredential`.
    ///
    /// # Arguments
    ///
    /// * `award_id` - The unique award identifier.
    /// * `bearer_token` - The caller's bearer token for authentication.
    ///
    /// # Errors
    ///
    /// Returns an error when the award is not found, access is forbidden, or
    /// an upstream service fails.
    fn get_ob3(
        &self,
        award_id: &str,
        bearer_token: &str,
    ) -> Result<OB3Award, super::client::AwardError>;
}

impl<C> AwardsClientPort for HttpAwardsClient<C>
where
    C: crate::helpers::http_client::HttpClient,
{
    fn get_ob3(
        &self,
        award_id: &str,
        bearer_token: &str,
    ) -> Result<OB3Award, super::client::AwardError> {
        self.get_ob3(award_id, bearer_token)
    }
}
