"""Tests for PostgreSQLRepositoryBase domain error wrapping."""

from unittest.mock import MagicMock, patch

import pytest

from src.lib.database_errors import DatabaseConnectionError, DatabaseQueryError
from src.lib.postgresql_base import PostgreSQLRepositoryBase


class TestPostgreSQLRepositoryBaseExecute:
    """Tests for execute() error wrapping."""

    def test_execute_wraps_connection_error_as_database_query_error(self) -> None:
        """execute() should wrap connection-level failures in DatabaseQueryError."""
        repo = PostgreSQLRepositoryBase("postgresql://localhost/test")
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = RuntimeError("connection lost")
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        repo._pool = mock_pool
        with pytest.raises(DatabaseQueryError, match="Query failed"):
            repo.execute("SELECT 1")

    def test_execute_wraps_generic_exception_as_database_query_error(self) -> None:
        """execute() should wrap any exception in DatabaseQueryError."""
        repo = PostgreSQLRepositoryBase("postgresql://localhost/test")
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = ValueError("something went wrong")
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        repo._pool = mock_pool
        with pytest.raises(DatabaseQueryError, match="Query failed"):
            repo.execute("SELECT 1")


class TestPostgreSQLRepositoryBaseInit:
    """Tests for __init__ connection error wrapping."""

    @patch("src.lib.postgresql_base.ConnectionPool")
    def test_init_wraps_connection_pool_error(
        self, mock_pool_class: MagicMock
    ) -> None:
        """__init__ should wrap connection pool failures in DatabaseConnectionError."""
        mock_pool_class.side_effect = RuntimeError("host unreachable")
        with pytest.raises(DatabaseConnectionError, match="Failed to connect"):
            PostgreSQLRepositoryBase("postgresql://localhost/test")