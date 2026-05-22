# ADR004: Use psycopg for PostgreSQL database access

| | |
|---|---|
| Status | draft |
| Date | 2026-05-20 |
| Deciders | Bèr Kessels, Thomas Kalverda |
| Consulted | See deciders |
| Informed | See deciders |

## Context and Problem Statement

We need a PostgreSQL database library for our repository adapters in the hexagonal architecture. The adapters must be simple, self-contained, and follow the ports and adapters pattern without introducing unnecessary complexity or app-wide database setup outside of these adapters.

## Decision Drivers

* Alignment with ports and adapters architecture
* Minimal dependencies and complexity
* Direct control over database operations
* Team familiarity and maintenance
* Avoid unnecessary abstraction layers

## Considered Options

* **psycopg** - Low-level PostgreSQL adapter
* **SQLAlchemy** - Industry-standard ORM with full database support
* **Records** - Simple ORM alternative
* **SQLAlchemy Core** - SQLAlchemy without ORM features

## Decision Outcome

Chosen option: **psycopg**, specifically `psycopg` with `psycopg_pool` for connection pooling.

The ports and adapters architecture works best with simple, self-contained adapters that directly implement the port interface. psycopg provides the low-level control we need while offering a clean, well-documented API for PostgreSQL operations.

### Consequences

* Good, because adapters remain simple and self-contained
* Good, because no ORM overhead or unnecessary abstractions
* Good, because minimal dependencies (psycopg is lightweight)
* Good, because almost all higher-level PostgreSQL libraries rely on psycopg anyway
* Good, because direct control over SQL, transactions, and connection management
* Neutral, because we manage connection/transaction/cursor boilerplate ourselves
* Bad, because we need to share common database utilities between adapters to avoid duplication

## Implementation Pattern

Each repository adapter follows this pattern:

1. Accepts a connection string in constructor
2. Creates its own connection pool using `psycopg_pool.ConnectionPool`
3. Implements port methods using `with pool.connection() as conn: with conn.cursor() as cursor:` pattern
4. Manages its own database schema initialization
5. Handles its own connection lifecycle (open/close)

This ensures each adapter is completely self-contained and has no dependencies on external database setup or configuration.

## Shared Utilities

To reduce duplication, connection management, transaction handling, and cursor operations should be extracted to shared helper functions or classes that adapters can use internally.

## Alternatives Considered

### SQLAlchemy (Full ORM)

**Rejected because**: SQLAlchemy is the industry standard but introduces significant overhead. It has many dependencies, supports numerous databases we will never use, and offers features (ORM, migrations, DSL) that we explicitly do not need. While it ultimately relies on psycopg for PostgreSQL, it adds unnecessary complexity and abstraction layers that conflict with our simple, direct adapter approach.

### Records

**Rejected because**: Records is a simpler ORM alternative, but it is still an ORM. We do not need object-relational mapping. Additionally, it is less widely used than SQLAlchemy, which raises concerns about long-term maintenance and community support.

### SQLAlchemy Core

**Rejected because**: SQLAlchemy Core removes the ORM layer but still includes a SQL expression language, multi-database support, and other features we do not require. While lighter than full SQLAlchemy, it remains a larger library than psycopg and introduces abstractions (like its DSL) that we do not need for our straightforward PostgreSQL usage.
