"""Unit tests for OfferService."""

from typing import override

import pytest

from src.offers.in_memory_adapter import InMemoryOffersRepository
from src.access_control.access_control_port import AccessControlPort
from src.offers.offer_service import (
    OfferService,
    PermissionDeniedError,
)
from tests.unit.test_doubles import (
    AccessControlStub,
    DenyingAccessControlStub,
    IssuerAgentSpy,
    IssuerAgentStub,
)

PUBLIC_URL = "https://issuer.example.com"


class TestOfferServiceCreateOffer:
    """Tests for OfferService.create_offer."""

    def test_returns_offer_with_correct_uri_format(self):
        """create_offer returns an Offer URI in the openid-credential-offer scheme."""
        service = OfferService(
            issuer_agent=IssuerAgentSpy(),
            access_control=AccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-123", bearer_token="tok")

        expected_prefix = f"openid-credential-offer://?credential_offer_uri={PUBLIC_URL}/api/v1/offers/"
        assert offer.uri.startswith(expected_prefix)
        assert offer.offer_id in offer.uri

    def test_returns_offer_with_achievement_id(self):
        """create_offer stores and returns the achievement_id on the offer."""
        service = OfferService(
            issuer_agent=IssuerAgentSpy(),
            access_control=AccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-456", bearer_token="tok")

        assert offer.achievement_id == "award-456"

    def test_stores_offer_in_repository(self):
        """create_offer persists the offer so it can be retrieved later."""
        repo = InMemoryOffersRepository()
        service = OfferService(
            issuer_agent=IssuerAgentSpy(),
            access_control=AccessControlStub(),
            offers_repository=repo,
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-789", bearer_token="tok")

        assert repo.get(offer.offer_id).offer_id == offer.offer_id

    def test_calls_issuer_agent_with_offer_id_and_achievement_id(self):
        """create_offer delegates to the issuer agent with the correct arguments."""
        agent = IssuerAgentSpy()
        service = OfferService(
            issuer_agent=agent,
            access_control=AccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-999", bearer_token="tok")

        assert len(agent.offers) == 1
        assert agent.offers[0] == (offer.offer_id, "award-999")

    def test_raises_permission_denied_when_access_control_denies(self):
        """create_offer raises PermissionDeniedError when access control denies."""
        service = OfferService(
            issuer_agent=IssuerAgentSpy(),
            access_control=DenyingAccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url=PUBLIC_URL,
        )

        with pytest.raises(PermissionDeniedError):
            _ = service.create_offer(achievement_id="award-123", bearer_token="tok")

    def test_checks_access_control_with_correct_arguments(self):
        """create_offer passes bearer token and resource details to access control."""

        class AccessControlSpy(AccessControlPort):
            """Spy: records calls to may_import."""

            calls: list[tuple[str, str, str, str]]

            def __init__(self) -> None:
                """Initialise with empty call log."""
                self.calls = []

            @override
            def may_import(
                self,
                bearer_token: str,
                resource_id: str,
                resource_type: str,
                permission: str,
            ) -> bool:
                """Record the call and grant permission."""
                self.calls.append(
                    (bearer_token, resource_id, resource_type, permission)
                )
                return True

        spy = AccessControlSpy()
        service = OfferService(
            issuer_agent=IssuerAgentSpy(),
            access_control=spy,
            offers_repository=InMemoryOffersRepository(),
            public_url=PUBLIC_URL,
        )

        _ = service.create_offer(achievement_id="award-123", bearer_token="my-token")

        assert spy.calls == [("my-token", "award-123", "Award", "import")]


class TestOfferServiceGetOffer:
    """Tests for OfferService.get_offer."""

    def test_get_offer_returns_stored_offer(self):
        """get_offer returns the offer that was previously created."""
        service = OfferService(
            issuer_agent=IssuerAgentSpy(),
            access_control=AccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url="https://issuer.example.com",
        )
        offer = service.create_offer(achievement_id="award-123", bearer_token="tok")

        result = service.get_offer(offer.offer_id)

        assert result.offer_id == offer.offer_id
        assert result.achievement_id == offer.achievement_id
        assert result.uri == offer.uri

    def test_get_offer_raises_key_error_for_unknown_id(self):
        """get_offer raises KeyError when the offer_id does not exist."""
        service = OfferService(
            issuer_agent=IssuerAgentStub(),
            access_control=AccessControlStub(),
            offers_repository=InMemoryOffersRepository(),
            public_url="https://issuer.example.com",
        )

        with pytest.raises(KeyError):
            _ = service.get_offer("nonexistent-id")
