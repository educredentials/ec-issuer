# Architecture Documentation

## Hexagonal Architecture Overview

This credential service implements **Hexagonal Architecture** (Ports and Adapters pattern), which provides clear separation between business logic and infrastructure concerns.

## Core Principles

### 1. Domain at the Center

The domain layer (`crates/domain/`) is the heart of the application:

- **Zero Infrastructure Dependencies**: No database, HTTP, or external service dependencies
- **Pure Business Logic**: Credential validation, issuance rules, revocation logic
- **Framework Agnostic**: Can be used in any context (HTTP, CLI, gRPC, etc.)

```rust
// Domain has NO dependencies on:
// - sqlx (database)
// - axum (HTTP)
// - tonic (gRPC)
// - any infrastructure crate

// Only uses:
// - serde (serialization - could be removed)
// - chrono (dates)
// - uuid (IDs)
```

### 2. Ports Define Interfaces

Ports (`crates/ports/`) define **contracts** between layers:

**Inbound Ports** (Use Cases):

```rust
#[async_trait]
pub trait IssueCredentialUseCase: Send + Sync {
    async fn execute(&self, request: IssueCredentialRequest)
        -> DomainResult<IssueCredentialResponse>;
}
```

**Outbound Ports** (Infrastructure Needs):

```rust
#[async_trait]
pub trait CredentialRepository: Send + Sync {
    async fn save(&self, credential: &Credential) -> DomainResult<()>;
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Credential>>;
    // ...
}
```

### 3. Adapters Implement Ports

Adapters (`crates/adapters/`) provide concrete implementations:

**Inbound Adapters** (Drivers):

- HTTP REST API (Axum)
- Could add: gRPC server, CLI, GraphQL, etc.

**Outbound Adapters** (Driven):

- PostgreSQL repository (SQLx)
- gRPC signing client (Tonic)
- HTTP clients for external services
- Event publishers

### 4. Dependency Direction

Dependencies always point **inward**:

```
Adapters ──depends on──> Ports ──depends on──> Domain

Domain NEVER depends on Ports or Adapters
```

This is enforced by Cargo dependencies:

- `domain/Cargo.toml`: No dependency on `ports` or `adapters`
- `ports/Cargo.toml`: Depends on `domain`, not `adapters`
- `adapters/Cargo.toml`: Depends on both `domain` and `ports`

## Layer Details

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

### Domain Layer

**Location**: `crates/domain/src/`

**Responsibilities**:

- Define domain entities (`Credential`, `Achievement`, `Issuer`)
- Implement business rules (validation, revocation, expiration)
- Define domain errors
- Value objects (status, formats, etc.)

**Key Files**:

- `entities.rs`: Core domain entities with behavior
- `value_objects.rs`: Immutable domain concepts
- `errors.rs`: Domain-specific errors

**Example**:

```rust
impl Credential {
    pub fn revoke(&mut self, reason: Option<String>) -> DomainResult<()> {
        // Business rule: cannot revoke already revoked credential
        if self.status.is_revoked() {
            return Err(DomainError::credential_already_revoked(self.id));
        }

        self.status = CredentialStatus::Revoked;
        self.revocation_info = Some(RevocationInfo::new(reason));
        self.updated_at = Utc::now();

        Ok(())
    }
}
```

### Ports Layer

**Location**: `crates/ports/src/`

**Responsibilities**:

- Define use case interfaces (inbound ports)
- Define infrastructure interfaces (outbound ports)
- Implement application services (use case orchestration)

**Key Files**:

- `inbound.rs`: Use case trait definitions
- `outbound.rs`: Infrastructure trait definitions
- `services.rs`: Application service implementations

**Example**:

```rust
pub struct CredentialService {
    repository: Arc<dyn CredentialRepository>,
    signing_client: Arc<dyn SigningClient>,
    achievement_client: Arc<dyn AchievementClient>,
    issuer_client: Arc<dyn IssuerClient>,
    event_publisher: Arc<dyn EventPublisher>,
    serializers: Vec<Arc<dyn CredentialSerializer>>,
}

#[async_trait]
impl IssueCredentialUseCase for CredentialService {
    async fn execute(&self, request: IssueCredentialRequest)
        -> DomainResult<IssueCredentialResponse>
    {
        // 1. Fetch external data
        let achievement = self.achievement_client.get_achievement(&request.achievement_id).await?;
        let issuer = self.issuer_client.get_issuer(&request.issuer_id).await?;

        // 2. Use domain logic to create credential
        let credential = CredentialBuilder::new()
            .credential_subject(subject)
            .achievement(achievement)
            .issuer(issuer)
            .build()?;

        // 3. Sign credential
        let proof = self.signing_client.sign(&credential).await?;
        credential.attach_proof(proof);

        // 4. Persist
        self.repository.save(&credential).await?;

        // 5. Publish event
        self.event_publisher.publish_credential_issued(&credential).await?;

        Ok(IssueCredentialResponse { credential })
    }
}
```

### Serializers Layer

**Location**: `crates/serializers/src/`

**Responsibilities**:

- Convert canonical domain model to format-specific representations
- Open Badges 3.0 (OB3) serialization
- European Learner Model (ELM) serialization

**Key Files**:

- `ob3.rs`: Open Badges 3.0 serializer
- `elm.rs`: European Learner Model serializer

**Example**:

```rust
impl CredentialSerializer for OB3Serializer {
    fn format(&self) -> CredentialFormat {
        CredentialFormat::OpenBadges3
    }

    fn serialize(&self, credential: &Credential) -> DomainResult<Value> {
        json!({
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://purl.imsglobal.org/spec/ob/v3p0/context.json"
            ],
            "type": ["VerifiableCredential", "OpenBadgeCredential"],
            "issuer": /* ... */,
            "credentialSubject": /* ... */,
        })
    }
}
```

### Adapters Layer

**Location**: `crates/adapters/src/`

**Responsibilities**:

- Implement inbound adapters (HTTP API)
- Implement outbound adapters (database, gRPC, HTTP clients)
- Handle infrastructure concerns (error translation, logging)

**Key Files**:

- `http/`: REST API with Axum
- `repository.rs`: PostgreSQL implementation
- `signing.rs`: Signing client implementations
- `clients.rs`: External API clients
- `events.rs`: Event publisher implementations

**Example - Repository**:

```rust
pub struct PostgresCredentialRepository {
    pool: PgPool,
}

#[async_trait]
impl CredentialRepository for PostgresCredentialRepository {
    async fn save(&self, credential: &Credential) -> DomainResult<()> {
        sqlx::query(/* SQL */)
            .bind(credential.id)
            .bind(/* ... */)
            .execute(&self.pool)
            .await?;

        Ok(())
    }
}
```

**Example - HTTP Handler**:

```rust
pub async fn issue_credential(
    State(state): State<AppState>,
    Json(request): Json<IssueCredentialRequest>,
) -> Result<(StatusCode, Json<IssueCredentialResponse>), ApiError> {
    // Call use case
    let response = state.issue_credential.execute(request).await?;
    Ok((StatusCode::CREATED, Json(response)))
}
```

## Dependency Injection

All wiring happens in `src/main.rs`:

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. Initialize outbound adapters
    let repository = Arc::new(PostgresCredentialRepository::new(pool));
    let signing_client = Arc::new(GrpcSigningClient::new(url));
    let achievement_client = Arc::new(InMemoryAchievementClient::new());
    let issuer_client = Arc::new(InMemoryIssuerClient::new());
    let event_publisher = Arc::new(StubEventPublisher::new());
    let serializers = vec![
        Arc::new(OB3Serializer::new()),
        Arc::new(ELMSerializer::new()),
    ];

    // 2. Create application service
    let credential_service = Arc::new(CredentialService::new(
        repository,
        signing_client,
        achievement_client,
        issuer_client,
        event_publisher,
        serializers,
    ));

    // 3. Create HTTP application state
    let app_state = AppState {
        issue_credential: credential_service.clone(),
        get_credential: credential_service.clone(),
        list_credentials: credential_service.clone(),
        revoke_credential: credential_service.clone(),
    };

    // 4. Start HTTP server
    let app = create_router(app_state);
    axum::serve(listener, app).await?;
}
```

## Testing Strategy

### Domain Layer Tests

Pure unit tests with no mocks needed:

```rust
#[test]
fn test_credential_revocation() {
    let mut credential = create_test_credential();

    assert!(credential.revoke(Some("Testing".to_string())).is_ok());
    assert_eq!(credential.status, CredentialStatus::Revoked);

    // Cannot revoke twice
    assert!(credential.revoke(None).is_err());
}
```

### Application Service Tests

Use mock implementations of ports:

```rust
#[tokio::test]
async fn test_issue_credential_use_case() {
    let mut mock_repo = MockCredentialRepository::new();
    mock_repo.expect_save()
        .times(1)
        .returning(|_| Ok(()));

    let service = CredentialService::new(
        Arc::new(mock_repo),
        // ... other mocks
    );

    let result = service.execute(request).await;
    assert!(result.is_ok());
}
```

### Adapter Tests

Integration tests with real infrastructure (test database, etc.)

## Benefits of This Architecture

### 1. Testability

- Domain: Pure unit tests
- Services: Mock ports
- Adapters: Integration tests

### 2. Flexibility

Swap implementations without changing domain:

```rust
// Development
let signing = Arc::new(InMemorySigningClient::new());

// Production
let signing = Arc::new(GrpcSigningClient::new(url));
```

### 3. Maintainability

- Clear boundaries between layers
- Changes to infrastructure don't affect business logic
- Easy to understand and navigate

### 4. Technology Independence

- Can migrate from PostgreSQL to MongoDB
- Can replace Axum with another HTTP framework
- Can add new adapters (gRPC, GraphQL) without touching domain

### 5. Business Logic Focus

Developers can work on domain logic without worrying about:

- Database details
- HTTP concerns
- External service protocols

## Common Patterns

### Pattern: Repository

Abstracts data persistence:

```rust
// Port
trait CredentialRepository {
    async fn save(&self, credential: &Credential) -> DomainResult<()>;
}

// Adapter
struct PostgresCredentialRepository { /* ... */ }
struct MongoCredentialRepository { /* ... */ }
struct InMemoryCredentialRepository { /* ... */ }
```

### Pattern: Service Layer

Orchestrates use cases:

```rust
struct CredentialService {
    // Dependencies injected
    repository: Arc<dyn CredentialRepository>,
    signing_client: Arc<dyn SigningClient>,
}

impl IssueCredentialUseCase for CredentialService {
    async fn execute(&self, request: IssueCredentialRequest) -> DomainResult<_> {
        // Orchestrate domain logic and infrastructure calls
    }
}
```

### Pattern: Domain Events

Decouple side effects from business logic:

```rust
// After credential issued
self.event_publisher.publish_credential_issued(&credential).await?;

// Adapter can implement this to:
// - Send email notification
// - Publish to message queue
// - Update search index
// - etc.
```

## Anti-Patterns to Avoid

### ❌ Domain Depending on Infrastructure

```rust
// WRONG - domain importing sqlx
use sqlx::PgPool;

impl Credential {
    pub async fn save(&self, pool: &PgPool) { /* ... */ }
}
```

### ❌ Business Logic in Adapters

```rust
// WRONG - validation logic in HTTP handler
pub async fn issue_credential(Json(req): Json<Request>) {
    if req.subject_id.is_empty() {
        return Err(/* validation error */);
    }
}
```

### ❌ Circular Dependencies

```rust
// WRONG - ports depending on adapters
use credential_adapters::PostgresRepo;
```

## Conclusion

Hexagonal architecture provides:

- **Clear separation** of concerns
- **Testable** business logic
- **Flexible** infrastructure
- **Maintainable** codebase
- **Technology independence**

The initial setup cost is higher, but the long-term benefits are significant for complex domains and evolving requirements.
