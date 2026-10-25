"""Config for e2e tests."""

from dataclasses import dataclass
import os


@dataclass
class Config:
    """E2E test configuration loaded from environment variables."""

    ec_issuer_url: str = os.environ["EC_ISSUER_URL"]
    ssi_agent_url: str = os.environ["SSI_AGENT_URL"]
    edc_ssi_agent_url: str = os.environ.get(
        "SSI_AGENT_EDC_URL", os.environ.get("SSI_AGENT_URL", "")
    )
