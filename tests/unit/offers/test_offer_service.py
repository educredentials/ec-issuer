"""Unit tests for OfferService."""

from typing import override

import pytest

from src.access_control.access_control_port import AccessControlPort
from src.metadata.metadata import CredentialIssuerMetadata, IssuerAgentPort
from src.offers.offer_service import (
    Offer,
    OfferService,
    OffersRepositoryPort,
    PermissionDeniedError,
)


class StubIssuerAgent(IssuerAgentPort):
    """Stub issuer agent that records create_offer calls."""

    offers: list[tuple[str, str]]

    def __init__(self):
        """Initialise with empty call log."""
        self.offers = []

    @override
    def credential_issuer_metadata(self) -> CredentialIssuerMetadata:
        """Unused in offer tests."""
        raise NotImplementedError

    @override
    def create_offer(self, offer_id: str, achievement_id: str) -> None:
        """Record the call."""
        self.offers.append((offer_id, achievement_id))


class StubOffersRepository(OffersRepositoryPort):
    """In-memory stub repository for testing."""

    stored: list[Offer]

    def __init__(self):
        """Initialise with empty store."""
        self.stored = []

    @override
    def store(self, offer: Offer) -> None:
        """Store an offer."""
        self.stored.append(offer)

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by id."""
        for offer in self.stored:
            if offer.offer_id == offer_id:
                return offer
        raise KeyError(offer_id)


class AllowingAccessControl(AccessControlPort):
    """Stub that always grants permission."""

    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        """Always return True."""
        return True


class DenyingAccessControl(AccessControlPort):
    """Stub that always denies permission."""

    @override
    def may_import(
        self,
        bearer_token: str,
        resource_id: str,
        resource_type: str,
        permission: str,
    ) -> bool:
        """Always return False."""
        return False


PUBLIC_URL = "https://issuer.example.com"


class TestOfferServiceCreateOffer:
    """Tests for OfferService.create_offer."""

    def test_returns_offer_with_correct_uri_format(self):
        """create_offer returns an Offer URI in the openid-credential-offer scheme."""
        service = OfferService(
            issuer_agent=StubIssuerAgent(),
            access_control=AllowingAccessControl(),
            offers_repository=StubOffersRepository(),
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-123", bearer_token="tok")

        expected_prefix = (
            f"openid-credential-offer://?credential_offer_uri={PUBLIC_URL}/api/v1/offers/"
        )
        assert offer.uri.startswith(expected_prefix)
        assert offer.offer_id in offer.uri

    def test_returns_offer_with_achievement_id(self):
        """create_offer stores and returns the achievement_id on the offer."""
        service = OfferService(
            issuer_agent=StubIssuerAgent(),
            access_control=AllowingAccessControl(),
            offers_repository=StubOffersRepository(),
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-456", bearer_token="tok")

        assert offer.achievement_id == "award-456"

    def test_stores_offer_in_repository(self):
        """create_offer persists the offer so it can be retrieved later."""
        repo = StubOffersRepository()
        service = OfferService(
            issuer_agent=StubIssuerAgent(),
            access_control=AllowingAccessControl(),
            offers_repository=repo,
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-789", bearer_token="tok")

        retrieved = repo.get(offer.offer_id)
        assert retrieved.offer_id == offer.offer_id

    def test_calls_issuer_agent_with_offer_id_and_achievement_id(self):
        """create_offer delegates to the issuer agent with the correct arguments."""
        agent = StubIssuerAgent()
        service = OfferService(
            issuer_agent=agent,
            access_control=AllowingAccessControl(),
            offers_repository=StubOffersRepository(),
            public_url=PUBLIC_URL,
        )

        offer = service.create_offer(achievement_id="award-999", bearer_token="tok")

        assert len(agent.offers) == 1
        assert agent.offers[0] == (offer.offer_id, "award-999")

    def test_raises_permission_denied_when_access_control_denies(self):
        """create_offer raises PermissionDeniedError when access control denies."""
        service = OfferService(
            issuer_agent=StubIssuerAgent(),
            access_control=DenyingAccessControl(),
            offers_repository=StubOffersRepository(),
            public_url=PUBLIC_URL,
        )

        with pytest.raises(PermissionDeniedError):
            _ = service.create_offer(achievement_id="award-123", bearer_token="tok")

    def test_checks_access_control_with_correct_arguments(self):
        """create_offer passes bearer token and resource details to access control."""

        class SpyAccessControl(AccessControlPort):
            """Records calls to may_import."""

            calls: list[tuple[str, str, str, str]]

            def __init__(self):
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

        spy = SpyAccessControl()
        service = OfferService(
            issuer_agent=StubIssuerAgent(),
            access_control=spy,
            offers_repository=StubOffersRepository(),
            public_url=PUBLIC_URL,
        )

        _ = service.create_offer(achievement_id="award-123", bearer_token="my-token")

        assert spy.calls == [("my-token", "award-123", "Award", "import")]
