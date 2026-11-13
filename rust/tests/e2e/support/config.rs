/// E2E test configuration.

use std::env;

#[derive(Clone)]
pub struct Config {
    /// Base URL of the ec-issuer service under test.
    pub ec_issuer_url: String,
    /// Base URL of the SSI agent.
    pub ssi_agent_url: String,
}

impl Config {
    pub fn new() -> Self {
        Self {
            ec_issuer_url: env::var("EC_ISSUER_URL").expect("EC_ISSUER_URL not set"),
            ssi_agent_url: env::var("TEST_SSI_AGENT_URL")
                .ok()
                .or_else(|| env::var("SSI_AGENT_URL").ok())
                .unwrap_or_else(|| "http://localhost:8001".to_string()),
        }
    }
}
