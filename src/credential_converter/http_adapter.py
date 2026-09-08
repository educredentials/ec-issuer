"""HTTP adapter for the credential converter."""

import base64
import binascii
import json
import logging

from typing import override

from src.lib.http_client import HttpClient, HttpResponse, RequestsHttpClient

from .credential_converter_port import (
    CredentialConverterClientError,
    CredentialConverterPort,
)

log = logging.getLogger(__name__)

CONVERSION_PATH = "/api"
PREFERRED_LANGUAGE = "en"


class HttpCredentialConverterAdapter(CredentialConverterPort):
    """Adapter that calls the converter's HTTP API.

    Encodes the input credential as base64, POSTs it to the converter, and
    decodes the JSON response.
    """

    _base_url: str
    _http_client: HttpClient

    def __init__(
        self,
        converter_base_url: str,
        http_client: HttpClient | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            converter_base_url: Base URL of the credential converter.
            http_client: The HTTP client. Defaults to requests module.
        """
        self._base_url = converter_base_url.rstrip("/")
        self._http_client = http_client or RequestsHttpClient()

    @override
    def convert(self, credential: dict[str, object]) -> dict[str, object]:
        """Convert an OB3 credential to ELM/EDC format.

        Args:
            credential: The OB3 credential as a dict.

        Returns:
            The converted ELM/EDC credential as a dict.

        Raises:
            CredentialConverterClientError: On any failure.
        """
        try:
            return self._do_convert(credential)
        except CredentialConverterClientError:
            raise
        except Exception as exc:
            raise CredentialConverterClientError(
                f"Unexpected error converting credential: {exc}"
            ) from exc

    def _do_convert(self, credential: dict[str, object]) -> dict[str, object]:
        """Execute the HTTP call to the converter.

        Args:
            credential: The OB3 credential as a dict.

        Returns:
            The converted ELM/EDC credential as a dict.

        Raises:
            CredentialConverterClientError: On network or converter errors.
        """
        content = self._encode_input(credential)
        payload = self._build_request(content)

        response = self._http_client.post(
            f"{self._base_url}{CONVERSION_PATH}",
            json=payload,
        )

        if response.status_code == 400:
            raise CredentialConverterClientError(
                f"Converter returned 400: {response.content.decode()}"
            )
        if 500 <= response.status_code < 600:
            raise CredentialConverterClientError(
                f"Converter returned {response.status_code}: "
                + response.content.decode()
            )
        if not (200 <= response.status_code < 300):
            raise CredentialConverterClientError(
                f"Converter returned unexpected status {response.status_code}"
            )

        return self._decode_response(response)

    def _encode_input(self, credential: dict[str, object]) -> str:
        """Base64-encode the input credential JSON.

        Args:
            credential: The OB3 credential as a dict.

        Returns:
            The base64-encoded string.
        """
        return base64.b64encode(json.dumps(credential).encode()).decode()

    def _build_request(self, content: str) -> dict[str, object]:
        """Build the converter request payload.

        Args:
            content: Base64-encoded input credential.

        Returns:
            The request dict for the converter API.
        """
        return {
            "From": {"Name": "OB", "Version": "3.0"},
            "To": {"Name": "elm", "Version": "3.2"},
            "Parameters": {"PreferredLanguages": [PREFERRED_LANGUAGE]},
            "Content": content,
        }

    def _decode_response(self, response: HttpResponse) -> dict[str, object]:
        """Decode the converter response and strip ``@context`` from the credential.

        Args:
            response: The HTTP response from the converter.

        Returns:
            The converted ELM/EDC credential as a dict (without ``@context``).

        Raises:
            CredentialConverterClientError: If response is malformed.
        """
        try:
            data = json.loads(response.content)  # pyright: ignore[reportAny]
        except json.JSONDecodeError as exc:
            raise CredentialConverterClientError(
                f"Invalid JSON response from converter: {exc}"
            ) from exc

        if "error" in data:
            raise CredentialConverterClientError(
                f"Converter error: {data['error']} - {data.get('message', '')}"  # pyright: ignore[reportAny]
            )

        if "content" not in data:
            raise CredentialConverterClientError(
                "Converter response missing 'content' field"
            )

        try:
            raw = base64.b64decode(data["content"])  # pyright: ignore[reportAny]
            credential = json.loads(raw)  # pyright: ignore[reportAny]
        except (binascii.Error, json.JSONDecodeError) as exc:
            raise CredentialConverterClientError(
                f"Failed to decode converter response: {exc}"
            ) from exc

        if not isinstance(credential, dict):
            raise CredentialConverterClientError(
                "Converter returned non-object credential"
            )
        credential.pop("@context", None)
        return credential