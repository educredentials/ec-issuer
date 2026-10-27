"""Domain-specific database errors.

All database exceptions in this project inherit from ``DatabaseError``,
making it possible to catch any database problem in a single except block.
"""


class DatabaseError(Exception):
    """Base class for database errors."""


class DatabaseConnectionError(DatabaseError):
    """Raised when the database connection pool fails to initialise."""


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""