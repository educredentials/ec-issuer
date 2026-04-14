# Architecture Documentation

## Hexagonal Architecture Overview

This credential service implements **Hexagonal Architecture** (Ports and Adapters pattern), which provides clear separation between business logic and infrastructure concerns.

**Practical Example**: See [`ports_adapters.py`](ports_adapters.md) for a complete working example demonstrating all key concepts with a simple jokes application. The accompanying [`ports_adapters_test.py`](ports_adapters_test.md) shows how the ports and adapters can be leveraged to test the application on several levels.

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
- Configuration loader
- Event publishers

### 4. Dependency Direction

Dependencies always point **inward**:

```
Adapters ──depends on──> Ports ──depends on──> Domain
```

Domain never depends on Ports or Adapters

## Layer Details

```
┌─────────────────────────────────────────────────────────────┐
│                   Adapters (Inbound)                        │
│                    HTTP API (Flask)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Ports (Inbound)                           │
│    Use Cases: Issue, Get, List, Revoke, Metadata            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Domain Layer                             │
│   Entities: Credential, Achievement, Issuer, Metadata       │
│   Business Logic: Validation, Revocation, Expiration        │
│   Value Objects: CredentialStatus, CredentialFormat         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Ports (Outbound)                          │
│   Interfaces (ABC): Repository, IssuerAgent, EventPublisher │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Adapters (Outbound)                       │
│   Database, Signing, HTTP Clients                           │
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

- Define use case interfaces (inbound ports) using Python's `ABC`
- Define infrastructure interfaces (outbound ports) using Python's `ABC`
- Implement application services (use case orchestration)

**Python Implementation Notes**:
- `ABC` provides runtime enforcement of abstract methods
- `@abstractmethod` decorator marks methods that must be implemented
- Type checkers like basedpyright verify interface compliance statically
- See `ports_adapters.py` for concrete examples using ABC

### Adapters Layer

**Responsibilities**:

- Implement inbound adapters (HTTP API)
- Implement outbound adapters (database, signing, HTTP clients)
- Handle infrastructure concerns (error translation, logging)

## Benefits of This Architecture

### 1. Testability

Hexagonal architecture enables simple, isolated testing without complex mocks or stubs:

**Unit Tests** - Test domain logic in complete isolation:
```python
# Test domain model without any infrastructure
content = "Why did the chicken cross the road. To get to the other side."
joke = Joke.from_content(content)
assert joke.title == "Why did the chicken cross the road."
assert joke.body == "To get to the other side."
```

**Integration Tests** - Test service layer with real adapters:
```python
# Test service with real InMemoryJokesRepository (no mocks needed)
repository = InMemoryJokesRepository()
service = JokeService(repository)
jokes = service.get_jokes()
assert len(jokes) == 0  # Starts empty
```

**End-to-End Tests** - Test complete application with real persistence:
```python
# Test actual CLI commands with file storage
# Cleanup first
shutil.rmtree("/tmp/jokes_db", ignore_errors=True)

# Test real command execution
output = subprocess.check_output([
    "python", "ports_adapters.py", "create", 
    "Test joke. Test body."
])

# Verify persistence
output = subprocess.check_output(["python", "ports_adapters.py", "list"])
assert "Test joke." in output.decode("utf-8")
```

**Key Testing Benefits**:
- Unit tests require **no mocks** - domain is pure Python
- Integration tests use **real adapters** - no complex stubbing
- End-to-end tests verify **real persistence** across process boundaries
- Adapters can be tested in isolation by implementing their port contract

**Note on End-to-End Testing**: While unit and integration tests focus on isolated components, end-to-end tests verify the complete application with all adapters working together as they would in production. These tests exercise the actual CLI commands, real file storage, and process boundaries to ensure the system works as a whole.

### 2. Type-Safe Development

- **Compile-time checking**: basedpyright catches interface violations early
- **Better IDE support**: Autocompletion works across layers
- **Refactoring safety**: Type system prevents breaking changes

**Example from ports_adapters.py**:
```python
# Type checker will catch if CommandlineJokesInteraction
# doesn't implement all methods from JokesInterationPort
jokes_interaction: JokesInterationPort = CommandlineJokesInteraction(joke_service)
```

### 2. Practical Flexibility

Swap implementations without changing domain:

```python
# Development - use in-memory implementations
repository = InMemoryJokesRepository()
service = JokeService(repository)

# Production - switch to real database
repository = DatabaseJokesRepository()
service = JokeService(repository)  # Same interface, different implementation
```

### 3. Real-World Maintainability

- **Clear layer boundaries**: Each file has a single responsibility
- **Easy testing**: Mock ports for unit testing, test adapters separately
- **Gradual migration**: Can introduce architecture incrementally

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

Abstracts data persistence using ABC (as shown in ports_adapters.py):

```python
from abc import ABC, abstractmethod

# Outbound Port (ABC)
class CredentialRepository(ABC):
    @abstractmethod
    async def save(self, credential: 'Credential') -> None: ...

    @abstractmethod
    async def find_by_id(self, id: str) -> 'Credential': ...

# Outbound Adapter
class DatabaseCredentialRepository(CredentialRepository):
    async def save(self, credential: 'Credential') -> None:
        # Save to database
        pass

    async def find_by_id(self, id: str) -> 'Credential':
        # Fetch from database
        pass
```

**Key differences from ports_adapters.py example**:
- Uses async methods for real-world applications
- Follows same ABC pattern as `JokesRepositoryPort`
- basedpyright will enforce all abstract methods are implemented

### Pattern: Use Case (Inbound Port)

Defines application operations using ABC (similar to ports_adapters.py):

```python
from abc import ABC, abstractmethod

# Inbound Port (ABC)
class IssueCredentialUseCase(ABC):
    @abstractmethod
    async def execute(self, request: 'IssueCredentialRequest') -> 'IssueCredentialResponse': ...

# Implementation (Application Service)
class CredentialService(IssueCredentialUseCase):
    def __init__(self, repository: CredentialRepository):
        self.repository = repository

    async def execute(self, request: 'IssueCredentialRequest') -> 'IssueCredentialResponse':
        credential = create_credential(request)
        await self.repository.save(credential)
        return IssueCredentialResponse(credential)

# Inbound Adapter (Flask Handler)
async def issue_credential_handler(request: 'IssueCredentialRequest') -> 'IssueCredentialResponse':
    service = CredentialService(DatabaseCredentialRepository())
    return await service.execute(request)
```

**Note**: This follows the same pattern as `JokeService` and `CommandlineJokesInteraction` in ports_adapters.py

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

## Type Safety with basedpyright

The architecture leverages Python's type system for compile-time safety:

```bash
# Run type checking
basedpyright src/

# Or for strict checking
basedpyright --strict src/
```

**Benefits**:
- Catches missing interface implementations
- Verifies dependency injection types
- Ensures adapter compatibility with ports
- Provides IDE autocompletion and refactoring support

## Practical Implementation Guide

### 1. Start with Domain
```python
# Define your core domain model first
class Credential:
    # Business logic and validation
    pass
```

### 2. Define Ports (Interfaces)
```python
# Create ABC interfaces for what your domain needs
class CredentialRepository(ABC):
    @abstractmethod
    def save(self, credential: Credential) -> None: ...
```

### 3. Implement Adapters
```python
# Create concrete implementations
class DatabaseCredentialRepository(CredentialRepository):
    def save(self, credential: Credential) -> None:
        # Actual database implementation
        pass
```

### 4. Create Application Service
```python
# Coordinate domain logic using dependency injection
class CredentialService:
    def __init__(self, repository: CredentialRepository):
        self.repository = repository
```

### 5. Add Inbound Adapters
```python
# Implement user-facing interfaces
class FlaskCredentialHandler:
    def __init__(self, service: CredentialService):
        self.service = service
```

## Conclusion

Hexagonal architecture provides:

- **Clear separation** of concerns
- **Type-safe** development with basedpyright
- **Flexible** infrastructure
- **Maintainable** codebase
- **Technology independence**

**Getting Started**: See [`ports_adapters.py`](ports_adapters.py) for a complete, working example you can run and experiment with.

The initial setup cost is higher, but the long-term benefits are significant for complex domains and evolving requirements. Start small and grow the architecture as needed.
