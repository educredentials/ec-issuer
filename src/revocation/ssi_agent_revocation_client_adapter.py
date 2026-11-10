"""SSI-Agent Adapter for credential revocation operations."""

from typing import override

from src.lib.http_client import HttpClient, RequestsHttpClient

from .revocation_client_port import (
    CredentialRevocationError,
    RevocationClientPort,
)


_REVOKE_PAYLOAD: dict[str, object] = {"credentialStatus": "INVALID"}


class SsiAgentRevocationClientAdapter(RevocationClientPort):
    """Adapter for SSI Agent credential revocation API."""

    _ssi_agent_base_url: str
    _http_client: HttpClient

    def __init__(
        self,
        ssi_agent_url: str,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            ssi_agent_url: The base URL of the SSI agent.
            http_client: The HTTP client to use for requests.
                Defaults to requests module.
        """
        self._ssi_agent_base_url = ssi_agent_url.rstrip("/")
        if http_client is not None:
            self._http_client = http_client
        else:
            self._http_client = RequestsHttpClient()

    @override
    def revoke(self, credential_id: str) -> None:
        """Revoke an issued credential by ID.

        Sends a PATCH request to /v0/credentials/{credential_id} with
        credentialStatus set to INVALID.

        Args:
            credential_id: The unique credential identifier to revoke.

        Raises:
            CredentialRevocationError: When the SSI agent returns a non-2xx.
        """
        url = f"{self._ssi_agent_base_url}/v0/credentials/{credential_id}"
        response = self._http_client.patch(url, json=_REVOKE_PAYLOAD)

        if 200 <= response.status_code < 300:
            return

        msg = f"Upstream error: {response.status_code} - {response.text}"
        raise CredentialRevocationError(msg)
