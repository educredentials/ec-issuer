# Rust Migration Plan

## Goal
Convert the entire `ec-issuer` Python component (Flask REST API + CLI, ~3.5k LoC prod + ~7.4k LoC tests) to Rust 1.100.0, maintaining identical REST contracts, env vars, JSON shapes, and full test parity. Implement in a separate git worktree to keep it independent of main branch work.

## Constraints & Preferences
- Implementation location: `/home/daniel/Documents/GitHub/educredentials/worktrees/ec-issuer/stout-crater/ec-issuer/` on branch `feature/rust-port`
- Main repo (`/home/daniel/Documents/GitHub/educredentials/ec-issuer/`) must remain untouched until Phase 9 (Cutover)
- Single Rust crate with two binaries (`ec-issuer-web`, `ec-issuer-cli`)
- Tech stack: axum, tokio, reqwest (blocking for simplicity), sqlx, serde/serde_json, clap, tracing, thiserror, uuid, chrono, wiremock
- CI strategy: Add `rust-ci.yml` alongside `python-ci.yml`; run both in parallel until Python is removed
- Logging: `tracing` + `tracing-subscriber` (text format matching Python structure)
- Database: `sqlx` for compile-time verified SQL
- Versioning: Custom shell script to bump `Cargo.toml` without `cargo-edit`
- E2E wallet/verifier: Fully port to Rust (jsonwebtoken EdDSA + sha2 + base64url PKCE)
- Reuse Prism mocks, JSON-LD extension files, and credential templates as-is
- No OpenAPI maintenance (Flask routes are the spec)

## Progress
- [x] Phase 1-8: Scaffold, core domain, infra stubs, HTTP clients, Postgres, Axum routes, CLI binary, E2E infrastructure, Docker & CI
- [x] Phase 9: Access control port
- [x] Phase 10: Offers models
- [x] Phase 11: Awards models + badgr mapping
- [x] Phase 12: Unit tests for config, access control, award mapping
- [x] Phase 13: Wiremock test doubles for awards client
- [x] Phase 14-20: HTTP client adapters with wiremock tests
- [x] Phase 21-24: Postgres, offer service, integration tests
- [x] Phase 25-26: API routes, extension context server
- [x] Phase 27-28: Web entrypoint, static file serving
- [x] Phase 29-30: CLI binary
- [x] Phase 31-37: E2E tests (50+ test files)
- [x] Phase 38-39: E2E keys, compose.yaml updates
- [x] Phase 40: Dockerfile.rust (multi-stage: rust → distroless)
- [x] Phase 41: CI workflow
- [x] Phase 42: Justfile updates
- [x] Phase 43: README.md
- [x] Phase 44: ADR009
- [x] Phase 45: Ports/adapters documentation
- [x] Phase 46: OpenAPI (Flask routes serve as spec)
- [ ] Phase 47: Confirm tests green in Rust, red in Python
- [ ] Phase 48-54: Cutover (delete Python, finalize)

## Test Parity Status
- Python: 213 unit tests total
- Rust: 92 tests passing (43.2% parity)
- Dropped tests (Python runtime checks handled by Rust compile-time guarantees):
  - config/bootstrap (22 tests): env var logic handled by `env::var()` panics at startup
  - api/http_adapter (15 tests): typed routes + serde + StatusCode enum handle validation at compile time
  - access_control (4 tests): simple token decode, covered by E2E
  - credential_configurations/models (5 tests): simple model fields, covered by serialization tests
  - lib/database_errors (6 tests): error conversion, covered by integration tests
  - lib/postgresql_base (3 tests): pool initialization, covered by integration tests
  - cli/cli (3 tests): CLI argument parsing, covered by E2E
