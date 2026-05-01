"""PostgreSQL adapter for the offers repository."""

from typing import cast, override

import psycopg2
from psycopg2.extensions import connection as _connection

from src.offers.offer_repository import Offer, OffersRepositoryPort


class PostgreSQLOffersRepository(OffersRepositoryPort):
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

    def _init_db(self) -> None:
        """Initialize the database table for offers."""
        with self._conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS offers (
                    offer_id TEXT PRIMARY KEY,
                    achievement_id TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    credential_issuer TEXT NOT NULL
                )
                """
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
                INSERT INTO offers (offer_id, achievement_id, uri, credential_issuer)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (offer_id) DO UPDATE
                SET achievement_id = EXCLUDED.achievement_id,
                    uri = EXCLUDED.uri,
                    credential_issuer = EXCLUDED.credential_issuer
                """,
                (
                    offer.offer_id,
                    offer.achievement_id,
                    offer.uri,
                    offer.credential_issuer,
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
                SELECT offer_id, achievement_id, uri, credential_issuer
                FROM offers
                WHERE offer_id = %s
                """,
                (offer_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise KeyError(f"Offer with id {offer_id} not found")
            return Offer(
                offer_id=cast(str, row[0]),
                achievement_id=cast(str, row[1]),
                uri=cast(str, row[2]),
                credential_issuer=cast(str, row[3]),
            )
