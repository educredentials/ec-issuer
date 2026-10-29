"""Config for e2e tests."""

from dataclasses import dataclass
import os


@dataclass
class Config:
    """E2E test configuration loaded from environment variables."""

    ec_issuer_url: str = os.environ["EC_ISSUER_URL"]
    # The SSI agent mock exposes localhost:8001 externally for credential offer URIs.
    # The ec-issuer (container) connects to mock-ssi-agent:4010 internally.
    ssi_agent_url: str = os.environ.get(
        "TEST_SSI_AGENT_URL", os.environ.get("SSI_AGENT_URL", "http://localhost:8001")
    )
