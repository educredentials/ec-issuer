# Credential Service - Hexagonal Architecture in Rust

Credential service that issues and signs **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

## Features

- **Issue Credentials**: Create and sign verifiable credentials
- **Multiple Formats**: Support for Open Badges 3.0 and European Learner Model
- **Revocation**: Revoke credentials with reason tracking
- **Expiration**: Automatic status updates for expired credentials
- **Digital Signatures**: Integration with signing service via gRPC
- **PostgreSQL Storage**: Full ACID compliance with SQLx
- **REST API**: Clean HTTP API with Axum
- **Type Safety**: Leverages Rust's type system for correctness

## Technology Stack

- **Axum**: High-performance HTTP server
- **SQLx**: Async PostgreSQL with compile-time query verification
- **Tonic**: gRPC framework
- **Tokio**: Async runtime
- **Serde**: Serialization/deserialization
- **Chrono**: Date/time handling
- **UUID**: Unique identifiers

## Getting Started

### Prerequisites

- Rust 1.75+
- PostgreSQL 14+
- (Optional) Signing service for production use

### Environment Variables

```bash
# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=3000

# Database configuration
DATABASE_URL=postgresql://postgres:postgres@localhost/credentials
DATABASE_MAX_CONNECTIONS=5

# Signing service configuration
SIGNING_USE_GRPC=false  # Set to true for gRPC signing service
SIGNING_SERVICE_URL=http://localhost:50051
```

### Running the Service

```bash
# Start PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_DB=credentials \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:14

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost/credentials

# Build and run
cargo build
cargo run
```

The service will start on `http://localhost:3000`

Now issue a credential:

```bash
curl -X POST http://localhost:3000/api/v1/credentials \
  -H "Authorization: Bearer FAKETOKEN"
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "did:example:alice123",
    "subject_name": "Alice Smith",
    "subject_email": "alice@example.com",
    "achievement_id": "achievement-1",
    "issuer_id": "issuer-1",
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

More API calls and details on the API structure, authorization and API documentation can be found in [docs/API.md](docs/API.md)

## Testing

```bash
cargo test --all
```

## Development

See [Way of Working](https://confluence.ia.surf.nl/spaces/EDUCRED/pages/260738891/Way+of+working+EduCredentials)

- Make a branch from `main`, e.g. feature/foozing-the-bars
- Add new \*_end to end_ tests for the feature in `tests` e.g. `tests/foozing_the_bars.rs`¹
- Start developing the feature in the appropriate module or modules:
  - Add unit tests to the module or modules where the feature is implemented: Unit tests live in the file or module that they test, not in separate files
  - Make the changes, repeat¹.
- Run tests before committing
- Use cargo clippy to check for code quality issues
- Use cargo fmt to format and lint
- Make a pull request against main.

```
cargo check --all
cargo test --all
cargo fmt --all
cargo clippy --all
```

## Extending the Service

### Adding a New Format

1. Create serializer in `crates/serializers/src/`:

```rust
pub struct MyFormatSerializer;

impl CredentialSerializer for MyFormatSerializer {
    fn format(&self) -> CredentialFormat {
        CredentialFormat::MyFormat
    }

    fn serialize(&self, credential: &Credential) -> DomainResult<Value> {
        // Implementation
    }
}
```

2. Register in `main.rs`:

```rust
let serializers = vec![
    Arc::new(OB3Serializer::new()),
    Arc::new(ELMSerializer::new()),
    Arc::new(MyFormatSerializer::new()), // Add here
];
```

### Adding a New Adapter

1. Implement the port trait in `crates/adapters/`
2. Wire it up in dependency injection (main.rs)
3. No changes to domain or ports needed!

## Production Considerations

- [ ] Enable TLS for database connections
- [ ] Implement proper gRPC signing client (currently stubbed)
- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Add comprehensive logging and metrics
- [ ] Set up distributed tracing
- [ ] Configure connection pooling
- [ ] Add circuit breakers for external services
- [ ] Implement credential caching strategy
- [ ] Set up backup and recovery procedures
