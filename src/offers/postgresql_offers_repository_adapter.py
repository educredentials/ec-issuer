"""PostgreSQL adapter for the offers repository."""

from typing import override

from psycopg.rows import class_row

from src.lib.postgresql_base import PostgreSQLRepositoryBase
from src.offers.models import Offer
from src.offers.offers_repository_port import OffersRepositoryPort


class PostgreSQLOffersRepositoryAdapter(PostgreSQLRepositoryBase, OffersRepositoryPort):
    """Adapter that stores offers in a PostgreSQL database."""

    def __init__(self, connection_string: str) -> None:
        """Initialise with a PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string.
        """
        PostgreSQLRepositoryBase.__init__(self, connection_string)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database table for offers."""
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS offers (
                offer_id TEXT PRIMARY KEY,
                award_id TEXT NOT NULL
            )
            """
            # TODO add indexes for offer_id and award_id
        )

    @override
    def store(self, offer: Offer) -> None:
        """Persist an offer in PostgreSQL.

        Args:
            offer: The offer to store.
        """
        self.execute(
            """
            INSERT INTO offers (offer_id, award_id)
            VALUES (%s, %s)
            ON CONFLICT (offer_id) DO UPDATE
            SET award_id = EXCLUDED.award_id
            """,
            (
                offer.offer_id,
                offer.award_id,
            ),
        )

    @override
    def get(self, offer_id: str) -> Offer:
        """Retrieve an offer by its identifier.

        Args:
            offer_id: The unique offer identifier.

        Returns:
            The matching Offer.

        Raises:
            KeyError: When no offer with the given id exists.
        """
        with self.conn() as conn:
            row = (
                conn.cursor(row_factory=class_row(Offer))
                .execute(
                    """
                SELECT offer_id, award_id, null AS uri
                FROM offers
                WHERE offer_id = %(id)s
                """,
                    {"id": offer_id},
                )
                .fetchone()
            )

        if row is None:
            raise KeyError(f"Offer with id {offer_id} not found")

        return row
