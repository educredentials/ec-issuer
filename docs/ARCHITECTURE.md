# Architecture Documentation

## Hexagonal Architecture Overview

This credential service implements **Hexagonal Architecture** (Ports and Adapters pattern), which provides clear separation between business logic and infrastructure concerns.

## Core Principles

### 1. Domain at the Center

The domain layer is the heart of the application:

- **Zero Infrastructure Dependencies**: No database, HTTP, or external service dependencies
- **Pure Business Logic**: Credential validation, issuance rules, revocation logic
- **Framework Agnostic**: Can be used in any context (HTTP, CLI, gRPC, etc.)

### 2. Ports Define Interfaces

Ports define **contracts** between layers:

**Inbound Ports** (Use Cases):
- Define interfaces for application operations (issue, get, list, revoke credentials)

**Outbound Ports** (Infrastructure Needs):
- Define interfaces for external interactions (persistence, signing, event publishing)

### 3. Adapters Implement Ports

Adapters provide concrete implementations:

**Inbound Adapters** (Drivers):
- HTTP REST API (Flask)
- Could add: gRPC server, CLI, GraphQL, etc.

**Outbound Adapters** (Driven):
- Database repository
- Signing client
- HTTP clients for external services
- Event publishers

### 4. Dependency Direction

Dependencies always point **inward**:

```
Adapters ──depends on──> Ports ──depends on──> Domain

Domain NEVER depends on Ports or Adapters
```

## Layer Details

```
┌─────────────────────────────────────────────────────────────┐
│                      Adapters (Inbound)                      │
│                    HTTP API (Flask)                         │
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
│   Database, Signing, HTTP Clients                            │
└─────────────────────────────────────────────────────────────┘
```

### Domain Layer

**Responsibilities**:

- Define domain entities (`Credential`, `Achievement`, `Issuer`)
- Implement business rules (validation, revocation, expiration)
- Define domain errors
- Value objects (status, formats, etc.)

### Ports Layer

**Responsibilities**:

- Define use case interfaces (inbound ports) using Python's Protocol
- Define infrastructure interfaces (outbound ports) using Python's Protocol
- Implement application services (use case orchestration)

### Adapters Layer

**Responsibilities**:

- Implement inbound adapters (HTTP API)
- Implement outbound adapters (database, signing, HTTP clients)
- Handle infrastructure concerns (error translation, logging)

## Benefits of This Architecture

### 1. Testability

- Domain: Pure unit tests
- Services: Mock ports
- Adapters: Integration tests

### 2. Flexibility

Swap implementations without changing domain:

```python
# Development
signing = InMemorySigningClient()

# Production
signing = GrpcSigningClient(url)
```

### 3. Maintainability

- Clear boundaries between layers
- Changes to infrastructure don't affect business logic
- Easy to understand and navigate

### 4. Technology Independence

- Can migrate from one database to another
- Can replace Flask with another HTTP framework
- Can add new adapters (gRPC, GraphQL) without touching domain

### 5. Business Logic Focus

Developers can work on domain logic without worrying about:

- Database details
- HTTP concerns
- External service protocols

## Common Patterns

### Pattern: Repository (Outbound Port)

Abstracts data persistence:

```python
from typing import Protocol

# Outbound Port (Protocol)
class CredentialRepository(Protocol):
    async def save(self, credential: 'Credential') -> None: ...
    async def find_by_id(self, id: str) -> 'Credential': ...

# Outbound Adapter
class DatabaseCredentialRepository:
    async def save(self, credential: 'Credential') -> None:
        # Save to database
        pass

    async def find_by_id(self, id: str) -> 'Credential':
        # Fetch from database
        pass
```

### Pattern: Use Case (Inbound Port)

Defines application operations:

```python
from typing import Protocol

# Inbound Port (Protocol)
class IssueCredentialUseCase(Protocol):
    async def execute(self, request: 'IssueCredentialRequest') -> 'IssueCredentialResponse': ...

# Inbound Adapter (Flask Handler)
async def issue_credential_handler(request: 'IssueCredentialRequest') -> 'IssueCredentialResponse':
    # Call use case implementation
    return await use_case.execute(request)
```

### Pattern: Service Layer

Orchestrates use cases:

```python
class CredentialService:
    def __init__(self, repository: CredentialRepository):
        self.repository = repository

    async def execute(self, request: 'IssueCredentialRequest') -> 'IssueCredentialResponse':
        # Use domain logic and infrastructure
        credential = create_credential(request)
        await self.repository.save(credential)
        return IssueCredentialResponse(credential)
```

### Pattern: Domain Events

Decouple side effects from business logic:

```python
# After credential issued
event_publisher.publish_credential_issued(credential)

# Adapter can implement this to:
# - Send email notification
# - Publish to message queue
# - Update search index
# - etc.
```

## Anti-Patterns to Avoid

### ❌ Domain Depending on Infrastructure

```python
# WRONG - domain importing database
from sqlalchemy import Session

class Credential:
    def save(self, session: Session):
        pass
```

### ❌ Business Logic in Adapters

```python
# WRONG - validation logic in HTTP handler
def issue_credential(request):
    if request.subject_id == "":
        raise ValidationError()
```

### ❌ Circular Dependencies

```python
# WRONG - ports depending on adapters
from adapters.repository import DatabaseRepository
```

## Conclusion

Hexagonal architecture provides:

- **Clear separation** of concerns
- **Testable** business logic
- **Flexible** infrastructure
- **Maintainable** codebase
- **Technology independence**

The initial setup cost is higher, but the long-term benefits are significant for complex domains and evolving requirements.
