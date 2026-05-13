"""PostgreSQL adapter for the offers repository."""

from typing import cast, override

import psycopg2
from psycopg2.extensions import connection as _connection

from src.offers.models import Offer
from src.offers.offers_repository_port import OffersRepositoryPort

class PostgreSQLOffersRepositoryAdapter(OffersRepositoryPort):
    """Adapter that stores offers in a PostgreSQL database."""

    _conn: _connection
    _connection_string: str

    def __init__(self, connection_string: str) -> None:
        """Initialise with a PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string.
        """
        self._connection_string = connection_string
        self._conn = psycopg2.connect(connection_string)
        self._init_db()

    def close_db(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def _init_db(self) -> None:
        """Initialize the database table for offers."""
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS offers (
                    offer_id TEXT PRIMARY KEY,
                    award_id TEXT NOT NULL
                )
                """
                # TODO add indexes for offer_id and award_id
            )
            self._conn.commit()

    @override
    def store(self, offer: Offer) -> None:
        """Persist an offer in PostgreSQL.

        Args:
            offer: The offer to store.
        """
        with self._conn.cursor() as cursor:
            cursor.execute(
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
            self._conn.commit()

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
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT offer_id, award_id
                FROM offers
                WHERE offer_id = %s
                """,
                (offer_id,),
            )
            row = cursor.fetchone()
        self._conn.commit()

        if row is None:
            raise KeyError(f"Offer with id {offer_id} not found")
        return Offer(
            offer_id=cast(str, row[0]),
            award_id=cast(str, row[1]),
            uri=None
        )
