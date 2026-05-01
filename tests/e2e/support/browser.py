"""Fake browser for simulating OIDC flows."""

from urllib.parse import parse_qs, urlparse


class Browser:
    """Fake browser to simulate OIDC flow."""

    def open(self, url: str) -> str:
        """Fakes user walking through OIDC flow and returning with an access token."""
        request_args = parse_qs(urlparse(url).query)

        fake_code = "fake_authorization_code"
        issuer_state = request_args["state"][0]
        redirect_uri = request_args["redirect_uri"][0]

        return f"{redirect_uri}?authorization_code={fake_code}&state={issuer_state}"
