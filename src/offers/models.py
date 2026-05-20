from dataclasses import dataclass


@dataclass
class Offer:
    """Domain model representing a credential offer."""

    offer_id: str
    award_id: str
    uri: str | None
