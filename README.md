# Credential Service - Hexagonal Architecture in Rust

A production-ready credential service that issues and signs **Open Badges 3.0** and **European Learner Model (ELM)** credentials, built with hexagonal architecture principles in Rust.

## Architecture Overview

This project strictly follows **Hexagonal Architecture** (also known as Ports and Adapters):

```
┌─────────────────────────────────────────────────────────────┐
│                      Adapters (Inbound)                      │
│                    HTTP API (Axum)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Ports (Inbound)                            │
│    Use Cases: Issue, Get, List, Revoke Credentials          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Domain Layer                              │
│   Entities: Credential, Achievement, Issuer                  │
│   Business Logic: Validation, Revocation, Expiration         │
│   Value Objects: CredentialStatus, CredentialFormat          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Ports (Outbound)                           │
│   Interfaces: Repository, SigningClient, EventPublisher      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Adapters (Outbound)                        │
│   PostgreSQL, gRPC Signing, HTTP Clients                     │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Domain Layer** (`crates/domain/`)
- Pure business logic with ZERO infrastructure dependencies
- Domain entities: `Credential`, `Achievement`, `Issuer`, `CredentialSubject`
- Value objects: `CredentialStatus`, `CredentialFormat`, `RevocationInfo`
- Domain errors and validation rules

**Ports Layer** (`crates/ports/`)
- **Inbound Ports**: Use case interfaces (traits) that define what the application does
- **Outbound Ports**: Infrastructure interfaces (traits) that define what the application needs
- Application services that implement use cases

**Serializers** (`crates/serializers/`)
- Format-specific serializers: OB3 (Open Badges 3.0), ELM (European Learner Model)
- Converts canonical domain model to format-specific JSON-LD

**Adapters Layer** (`crates/adapters/`)
- **Inbound Adapters**: HTTP API (Axum REST controllers)
- **Outbound Adapters**: PostgreSQL repository, gRPC signing client, HTTP clients

## Project Structure

```
credential-service/
├── Cargo.toml                      # Workspace root
├── src/
│   ├── main.rs                     # Application entry point (DI wiring)
│   └── config.rs                   # Configuration management
├── crates/
│   ├── domain/                     # Domain layer (pure business logic)
│   │   ├── src/
│   │   │   ├── entities.rs         # Credential entity
│   │   │   ├── value_objects.rs    # Value objects
│   │   │   └── errors.rs           # Domain errors
│   │   └── Cargo.toml
│   ├── ports/                      # Ports (interfaces)
│   │   ├── src/
│   │   │   ├── inbound.rs          # Use case interfaces
│   │   │   ├── outbound.rs         # Infrastructure interfaces
│   │   │   └── services.rs         # Application services
│   │   └── Cargo.toml
│   ├── serializers/                # Format serializers
│   │   ├── src/
│   │   │   ├── ob3.rs              # Open Badges 3.0
│   │   │   └── elm.rs              # European Learner Model
│   │   └── Cargo.toml
│   └── adapters/                   # Infrastructure adapters
│       ├── src/
│       │   ├── http/               # HTTP API (Axum)
│       │   ├── repository.rs       # PostgreSQL repository
│       │   ├── signing.rs          # gRPC signing client
│       │   ├── clients.rs          # External API clients
│       │   └── events.rs           # Event publisher
│       └── Cargo.toml
└── README.md
```

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
cargo build --release
cargo run --release
```

The service will start on `http://localhost:3000`

### Running Tests

```bash
# Run all tests
cargo test

# Run tests for specific crate
cargo test -p credential-domain
cargo test -p credential-ports
cargo test -p credential-serializers
```

## API Reference

### Issue Credential

**POST** `/api/v1/credentials`

```json
{
  "subject_id": "did:example:recipient123",
  "subject_name": "Alice Smith",
  "subject_email": "alice@example.com",
  "achievement_id": "achievement-1",
  "issuer_id": "issuer-1",
  "expires_at": "2025-12-31T23:59:59Z",
  "metadata": {}
}
```

Response: `201 Created`

### Get Credential

**GET** `/api/v1/credentials/:id?format=ob3`

Query parameters:
- `format`: Optional. Values: `ob3` (Open Badges 3.0), `elm` (European Learner Model)

Response: `200 OK` with credential in requested format

### List Credentials

**GET** `/api/v1/credentials?subject_id=did:example:123&limit=10`

Query parameters:
- `subject_id`: Filter by subject
- `issuer_id`: Filter by issuer
- `achievement_id`: Filter by achievement
- `status`: Filter by status (active, revoked, expired)
- `limit`: Max results (default: 100)
- `offset`: Pagination offset

Response: `200 OK`

### Revoke Credential

**POST** `/api/v1/credentials/:id/revoke`

```json
{
  "reason": "Credential no longer valid"
}
```

Response: `200 OK`

### Health Check

**GET** `/health`

Response: `200 OK`

## Hexagonal Architecture Benefits

### 1. Domain Independence
The domain layer has **zero dependencies** on infrastructure. You can change databases, HTTP frameworks, or signing services without touching business logic.

### 2. Testability
Each layer can be tested independently:
- Domain: Pure unit tests
- Ports: Interface contracts
- Adapters: Integration tests with mocks

### 3. Flexibility
Swap implementations easily:
```rust
// Development: Use in-memory signing
Arc::new(InMemorySigningClient::new())

// Production: Use gRPC signing service
Arc::new(GrpcSigningClient::new(url))
```

### 4. Clear Boundaries
Dependencies flow inward:
```
Adapters → Ports → Domain
```
The domain never depends on outer layers.

## Design Patterns Used

1. **Dependency Injection**: All dependencies passed via constructors
2. **Repository Pattern**: Abstracts data persistence
3. **Service Layer**: Orchestrates use cases
4. **Builder Pattern**: Fluent credential creation
5. **Value Objects**: Immutable domain concepts
6. **Domain Events**: Publish credential lifecycle events

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

## License

This is a demonstration project for hexagonal architecture in Rust.
