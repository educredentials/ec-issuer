"""Config for e2e tests."""


from dataclasses import dataclass
import os


@dataclass
class Config:
    """E2E test configuration loaded from environment variables."""

    public_url: str = os.environ["PUBLIC_URL"]
    ssi_agent_url: str = os.environ["SSI_AGENT_URL"]
