from dataclasses import dataclass

from enum import StrEnum


class CredentialType(StrEnum):
    """Credential type identifiers derived from ``dataModel`` field values."""

    OB3 = "open_badges_3-0"
    EDC = "european_learning_model_v3-3"

    @classmethod
    def by_short(cls, short: str) -> "CredentialType":
        """Resolve a short form (``ob3``/``edc``) to the full value.

        Args:
            short: The short form credential type.

        Returns:
            The matching CredentialType enum value.

        Raises:
            ValueError: When the short form is not recognised.
        """
        mapping = {"ob3": cls.OB3, "edc": cls.EDC}
        if short not in mapping:
            raise ValueError(
                f"Unknown short credential type: {short!r}. "
                + "Must be 'ob3' or 'edc'."
            )
        return mapping[short]


def is_known_credential_type(value: str) -> CredentialType:
    """Validate and coerce a dataModel string to CredentialType.

    Args:
        value: The dataModel string to validate (e.g. ``"open_badges_3-0"``).

    Returns:
        The matching CredentialType enum value.

    Raises:
        ValueError: When the value is not a known credential type.
    """
    for ct in CredentialType:
        if ct.value == value:
            return ct
    raise ValueError(
        f"Unknown credential type: {value!r}. "
        + "Must be 'open_badges_3-0' or 'european_learning_model_v3-3'."
    )


@dataclass
class Offer:
    """Domain model representing a credential offer."""

    offer_id: str
    award_id: str
    uri: str | None
