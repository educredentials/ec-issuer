"""Base class for PostgreSQL repository adapters."""

from typing import LiteralString

from psycopg import sql as psycopg_sql
from psycopg.abc import Params
from psycopg_pool import ConnectionPool

from .database_errors import DatabaseConnectionError, DatabaseQueryError


class PostgreSQLRepositoryBase:
    """Base class providing PostgreSQL connection pooling and query helpers."""

    _pool: ConnectionPool
    _connection_string: str

    def __init__(self, connection_string: str) -> None:
        """Initialise with a PostgreSQL connection string.

        Args:
            connection_string: PostgreSQL connection string.

        Raises:
            DatabaseConnectionError: When the connection pool fails to
                initialise (e.g. the database is unreachable).
        """
        self._connection_string = connection_string
        try:
            self._pool = ConnectionPool(
                conninfo=connection_string,
                open=True,
                min_size=1,
                max_size=10,
                timeout=30,
            )
        except Exception as exc:
            raise DatabaseConnectionError(
                f"Failed to connect to database: {exc}"
            ) from exc

    def execute(self, sql: LiteralString, params: Params = ()) -> None:
        """Execute a SQL statement with commit.

        Args:
            sql: The SQL statement to execute.
            params: Parameters for the SQL statement.

        Raises:
            DatabaseQueryError: When the SQL statement fails.
        """
        try:
            with self._pool.connection() as conn:
                # `sql` is LiteralString (compile-time constant) and
                # `params` are parameterised, so this is safe against injection.
                _ = conn.execute(psycopg_sql.SQL(sql), params)  # noqa: S608
                conn.commit()
        except Exception as exc:
            raise DatabaseQueryError(
                f"Query failed: {exc}"
            ) from exc

    def conn(self):
        """Return a connection context manager for manual query execution.

        Returns:
            A psycopg connection context manager.
        """
        return self._pool.connection()

    def close_db(self) -> None:
        """Close the database connection pool."""
        self._pool.close()
