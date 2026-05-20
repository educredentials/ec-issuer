"""Base class for PostgreSQL repository adapters."""

from typing import LiteralString

from psycopg.abc import Params
from psycopg_pool import ConnectionPool


class PostgreSQLRepositoryBase:
    """Base class providing PostgreSQL connection pooling and query helpers."""

    _pool: ConnectionPool
    _connection_string: str

    def __init__(self, connection_string: str) -> None:
        """Initialise with a PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string.
        """
        self._connection_string = connection_string
        self._pool = ConnectionPool(
            conninfo=connection_string,
            open=True,
            min_size=1,
            max_size=10,
        )

    def execute(self, sql: LiteralString, params: Params = ()) -> None:
        """Execute a SQL statement with commit.

        Args:
            sql: The SQL statement to execute.
            params: Parameters for the SQL statement.
        """
        with self._pool.connection() as conn:
            with conn.cursor() as cursor:
                _ = cursor.execute(sql, params)
                conn.commit()

    def conn(self):
        """Execute a SQL statement and return a single row.

        Args:
            sql: The SQL statement to execute.
            params: Parameters for the SQL statement.

        Returns:
            A single row as a tuple, or None if no results.
        """
        return self._pool.connection()

    def close_db(self) -> None:
        """Close the database connection pool."""
        self._pool.close()
