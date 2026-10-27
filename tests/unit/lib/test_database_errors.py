"""Tests for domain-specific database error classes."""

import pytest

from src.lib.database_errors import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseQueryError,
)


class TestDatabaseErrors:
    """Tests for the DatabaseError hierarchy."""

    def test_database_error_is_exception(self):
        """DatabaseError must be catchable as Exception."""
        with pytest.raises(Exception):
            raise DatabaseError("test")

    def test_database_connection_error_inherits_database_error(self):
        """DatabaseConnectionError inherits from DatabaseError."""
        with pytest.raises(DatabaseError):
            raise DatabaseConnectionError("connection failed")

    def test_database_query_error_inherits_database_error(self):
        """DatabaseQueryError inherits from DatabaseError."""
        with pytest.raises(DatabaseError):
            raise DatabaseQueryError("query failed")

    def test_database_connection_error_message(self):
        """DatabaseConnectionError preserves the error message."""
        msg = "connection refused"
        exc = DatabaseConnectionError(msg)
        assert str(exc) == msg

    def test_database_query_error_message(self):
        """DatabaseQueryError preserves the error message."""
        msg = "syntax error at SELECT"
        exc = DatabaseQueryError(msg)
        assert str(exc) == msg

    def test_catch_database_error_catches_subclasses(self):
        """A single except DatabaseError catches all subclasses."""
        caught = []
        for exc_class in (DatabaseConnectionError, DatabaseQueryError):
            try:
                raise exc_class("fail")
            except DatabaseError as e:
                caught.append(type(e).__name__)
        assert caught == ["DatabaseConnectionError", "DatabaseQueryError"]