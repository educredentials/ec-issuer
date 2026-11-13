# ADR-009: Rust Migration

## Status
Accepted

## Context
The `ec-issuer` service is currently implemented in Python using Flask, psycopg2, and other Python libraries. The service issues Open Badges 3.0 and European Learner Model (ELM) credentials.

We need to migrate to Rust to improve:
- Performance: Rust's zero-cost abstractions and compile-time guarantees reduce runtime overhead
- Reliability: Static typing and ownership model prevent entire classes of bugs
- Security: Memory safety without garbage collector
- Developer experience: Compile-time error detection reduces debugging time

## Decision
We will migrate the `ec-issuer` service from Python to Rust, implementing in a separate git worktree (`stout-crater`) on branch `feature/rust-port`.

### Tech Stack
- **Web framework**: axum (modern, type-safe, async-ready)
- **Database**: sqlx (compile-time SQL verification, connection pooling)
- **HTTP client**: reqwest (blocking client for simpler trait implementation)
- **Serialization**: serde/serde_json (consistent with Python JSON shapes)
- **CLI**: clap (command-line argument parsing)
- **Logging**: tracing + tracing-subscriber (structured logging)
- **Error handling**: thiserror (ergonomic error types)

### Implementation Strategy
1. Implement in git worktree to keep main branch stable
2. Parallel CI: run both Python and Rust CI until cutover
3. Maintain identical REST contracts, env vars, and JSON shapes
4. Port tests to achieve parity with Python test suite

### Cutover Strategy
1. Run both Python and Rust services in parallel
2. Gradually switch traffic from Python to Rust
3. Remove Python codebase once Rust is fully verified
4. Delete Python CI workflows, Dockerfiles, and dependencies

## Consequences
- **Positive**: Improved performance, reliability, and developer experience
- **Negative**: Learning curve for team, initial migration effort
- **Mitigation**: Comprehensive testing, parallel CI, gradual cutover
