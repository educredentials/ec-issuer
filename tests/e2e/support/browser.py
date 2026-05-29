"""Fake browser for simulating OIDC flows."""

from requests import request


class Browser:
    """Fake browser to simulate OIDC flow."""

    def open(self, url: str) -> str:
        """Fakes user walking through OIDC flow and returning with an access token."""
        # Open "url" with Request. Follow any redirects.
        # Until we have a redirect to an url that starts with mywallet:// in which case
        # we return that url.
        # For that, we cannot use the allow_redirects, because that would make "request"
        # attempt to GET that mywallet:// url, which it cannot
        current_url = url
        while True:
            resp = request(
                "GET",
                current_url,
                headers={"Accept": "text/html"},
                allow_redirects=False,
            )
            if resp.status_code not in (301, 302, 303, 307, 308):
                raise AssertionError(
                    f"Expected redirect, got {resp.status_code}: {resp.text[:200]}"
                )
            location = resp.headers["Location"]
            if location.startswith("mywallet://"):
                return location
            current_url = location
