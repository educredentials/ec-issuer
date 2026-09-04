"""Unit tests for HttpCredentialConverterAdapter."""

import base64
import json
from dataclasses import asdict

import pytest

from src.awards.models import (
    Achievement,
    AchievementSubject,
    Criteria,
    Issuer,
    OB3Award,
)
from src.credential_converter.credential_converter_port import (
    CredentialConverterClientError,
)
from typing import cast

from src.credential_converter.http_adapter import (
    HttpCredentialConverterAdapter,
)

from tests.unit.support.requests_doubles import (
    MockResponse,
    RequestsSpy,
)

# A minimal OB3 award used for encoding the request payload.
_SAMPLE_OB3_AWARD: OB3Award = OB3Award(
    id="http://example.com/awards/1",
    type=["VerifiableCredential", "OpenBadgeCredential"],
    name="Teamwork Badge",
    issuer=Issuer(
        id="http://example.com/issuers/1",
        type=["Profile"],
        name="Example Corp",
    ),
    validFrom="2024-01-01T00:00:00Z",
    credentialSubject=AchievementSubject(
        id="did:example:subject",
        type=["AchievementSubject"],
        achievement=Achievement(
            id="http://example.com/achievements/1",
            type=["Achievement"],
            criteria=Criteria(narrative="Work well with others."),
            description="Demonstrates teamwork.",
            name="Teamwork",
        ),
    ),
)


@pytest.fixture
def http_spy() -> RequestsSpy:
    """Provide a fresh RequestsSpy for each test."""
    return RequestsSpy()


@pytest.fixture
def subject(http_spy: RequestsSpy) -> HttpCredentialConverterAdapter:
    """Provide the adapter wired to the spy."""
    return HttpCredentialConverterAdapter(
        converter_base_url="http://converter:8080",
        http_client=http_spy,
    )


def _make_success_response(data: dict[str, object]) -> MockResponse:
    """Return a 200 response with base64-encoded ``data``."""
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    return MockResponse(
        status_code=200,
        _content=json.dumps({"content": encoded}).encode(),
    )


class TestHttpCredentialConverterAdapterSuccess:
    """Tests for the happy-path conversion flow."""

    def test_sends_correct_payload(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() POSTs the expected request structure."""
        http_spy.set_response(_make_success_response({}))
        _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

        call = http_spy.calls[0]
        assert call.method == "post"
        assert call.url == "http://converter:8080/api"
        assert call.json is not None
        payload = cast(dict[str, object], call.json)
        assert payload["From"] == {"Name": "OB", "Version": "3.0"}
        assert payload["To"] == {"Name": "elm", "Version": "3.2"}
        assert payload["Parameters"] == {
            "PreferredLanguages": ["en"]
        }
        assert "Content" in payload

    def test_decodes_base64_response(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() decodes the base64-encoded credential from the response."""
        response_credential = {
            "type": ["VerifiableCredential", "EuropeanDigitalCredential"],
            "credentialSubject": {"id": "did:example:sub"},
        }
        http_spy.set_response(_make_success_response(response_credential))

        result = subject.convert(asdict(_SAMPLE_OB3_AWARD))

        assert result == response_credential

    def test_strips_context_from_response(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() removes ``@context`` from the decoded credential."""
        response_credential = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "type": ["VerifiableCredential", "EuropeanDigitalCredential"],
            "credentialSubject": {"id": "did:example:sub"},
        }
        http_spy.set_response(_make_success_response(response_credential))

        result = subject.convert(asdict(_SAMPLE_OB3_AWARD))

        assert "@context" not in result
        cred_type = cast(list[object], result["type"])
        assert cred_type == ["VerifiableCredential",
                             "EuropeanDigitalCredential"]
        cred_subj = result["credentialSubject"]
        assert cred_subj == {"id": "did:example:sub"}


class TestHttpCredentialConverterAdapterErrors:
    """Tests for error responses from the converter."""

    def test_400_raises_client_error(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises CredentialConverterClientError on 400."""
        http_spy.set_response(
            MockResponse(status_code=400, _content=b'"Bad request"')
        )

        with pytest.raises(
            CredentialConverterClientError, match="Converter returned 400"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

    def test_500_raises_client_error(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises CredentialConverterClientError on 5xx."""
        http_spy.set_response(
            MockResponse(status_code=502, _content=b'"Bad Gateway"')
        )

        with pytest.raises(
            CredentialConverterClientError, match="Converter returned 502"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

    def test_unexpected_status_raises_client_error(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises on non-2xx/non-4xx/non-5xx."""
        http_spy.set_response(
            MockResponse(status_code=401, _content=b'"Unauthorized"')
        )

        with pytest.raises(
            CredentialConverterClientError,
            match="Converter returned unexpected status 401",
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

    def test_error_field_raises_client_error(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises on JSON response containing ``error`` field."""
        resp = {
            "error": "conversion_failed",
            "message": "invalid input",
            "content": "",
        }
        http_spy.set_response(
            MockResponse(
                status_code=200,
                _content=json.dumps(resp).encode(),
            )
        )

        with pytest.raises(
            CredentialConverterClientError,
            match="Converter error: conversion_failed",
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

    def test_missing_content_field_raises(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises when response JSON lacks ``content``."""
        http_spy.set_response(
            MockResponse(
                status_code=200,
                _content=json.dumps({"data": "ok"}).encode(),
            )
        )

        with pytest.raises(
            CredentialConverterClientError, match="missing 'content'"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))


class TestHttpCredentialConverterAdapterMalformed:
    """Tests for malformed converter responses."""

    def test_invalid_json_raises_client_error(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises on non-JSON response body."""
        http_spy.set_response(
            MockResponse(status_code=200, _content=b"not json")
        )

        with pytest.raises(
            CredentialConverterClientError, match="Invalid JSON"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

    def test_invalid_base64_raises_client_error(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises when the content is not valid base64."""
        http_spy.set_response(
            MockResponse(
                status_code=200,
                _content=json.dumps({"content": "!!!invalid!!!"}).encode(),
            )
        )

        with pytest.raises(
            CredentialConverterClientError, match="Failed to decode"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))

    def test_invalid_credential_json_raises(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises when decoded content is not valid JSON."""
        bad_json_bytes = b"this is not json"
        encoded = base64.b64encode(bad_json_bytes).decode()
        http_spy.set_response(
            MockResponse(
                status_code=200,
                _content=json.dumps({"content": encoded}).encode(),
            )
        )

        with pytest.raises(
            CredentialConverterClientError, match="Failed to decode"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))


    def test_non_object_credential_raises(
        self,
        http_spy: RequestsSpy,
        subject: HttpCredentialConverterAdapter,
    ) -> None:
        """convert() raises when the decoded credential is not a JSON object."""
        encoded = base64.b64encode(b'null').decode()
        http_spy.set_response(
            MockResponse(
                status_code=200,
                _content=json.dumps({"content": encoded}).encode(),
            )
        )
        with pytest.raises(
            CredentialConverterClientError, match="non-object credential"
        ):
            _ = subject.convert(asdict(_SAMPLE_OB3_AWARD))


class TestHttpCredentialConverterAdapterInit:
    """Tests for adapter initialization."""

    def test_strips_trailing_slash(self) -> None:
        """__init__() strips trailing slash from the base URL."""
        adapter = HttpCredentialConverterAdapter(
            converter_base_url="http://converter:8080/"
        )
        assert adapter._base_url == "http://converter:8080"  # pyright: ignore[reportPrivateUsage]

    def test_preserves_no_trailing_slash(self) -> None:
        """__init__() preserves URL without trailing slash."""
        adapter = HttpCredentialConverterAdapter(
            converter_base_url="http://converter:8080"
        )
        assert adapter._base_url == "http://converter:8080"  # pyright: ignore[reportPrivateUsage]

    def test_uses_default_http_client(self) -> None:
        """__init__() creates RequestsHttpClient when none is provided."""
        adapter = HttpCredentialConverterAdapter(
            converter_base_url="http://converter:8080"
        )
        # Should not raise — confirms default client was created
        assert adapter._http_client is not None  # pyright: ignore[reportPrivateUsage]