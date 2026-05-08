# ADR002: Use ABC instead of Protocol for Interface Definition

| | |
|---|---|
| Status | accepted |
| Date | 2024-07-15 |
| Deciders | Bèr Kessels, Daniel Ostkamp, Thomas Kalverda |
| Consulted | See deciders |
| Informed | See deciders |

## Context and Problem Statement

We need to enforce interface contracts in our hexagonal architecture implementation. Python offers two main approaches:
- `typing.Protocol` (structural typing, duck typing with type hints)
- `abc.ABC` with `@abstractmethod` (nominal typing, abstract base classes)

Both approaches work with type checkers like basedpyright, but they have different characteristics.

## Decision Drivers

* Development-time feedback and IDE support
* Runtime enforcement capabilities
* Team familiarity and learning curve
* Consistency with existing codebase patterns
* Type checker compatibility and strictness

## Considered Options

* Option 1: Use `typing.Protocol` for all interfaces
* Option 2: Use `abc.ABC` with `@abstractmethod` for all interfaces
* Option 3: Mix both approaches based on context

## Decision Outcome

Chosen option: "Use `abc.ABC` with `@abstractmethod` for all interfaces", as demonstrated in `ports_adapters.py`.

### Positive Consequences

* **Better development-time checks**: ABC provides clearer error messages in IDEs and type checkers
* **Runtime enforcement**: Abstract methods cannot be instantiated, catching errors earlier
* **Explicit contracts**: `@abstractmethod` makes interface requirements visibly explicit
* **Consistency**: Single approach throughout codebase reduces cognitive load
* **basedpyright compatibility**: Works well with our chosen type checker
* **Familiar pattern**: More Python developers are familiar with ABC than Protocol

### Negative Consequences

* **Nominal typing**: Less flexible than structural typing (classes must explicitly inherit)
* **Slightly more boilerplate**: Requires explicit inheritance and decorators
* **Runtime overhead**: Minimal but present abstract method checking

## Rationale

While Protocol offers more flexibility through structural typing, ABC provides better development-time feedback which aligns with our goal of catching errors early. The explicit nature of ABC interfaces makes the code more self-documenting and easier to understand for team members.

The `ports_adapters.py` example demonstrates this approach effectively:

```python
from abc import ABC, abstractmethod

class JokesRepositoryPort(ABC):
    """Outbound Port interface using ABC"""
    @abstractmethod
    def get_jokes(self) -> list[Joke]: ...

    @abstractmethod
    def create_joke(self, joke: Joke) -> Joke: ...

# Type checker and runtime both enforce implementation
class InMemoryJokesRepository(JokesRepositoryPort):
    def get_jokes(self) -> list[Joke]:
        return self.jokes
    
    def create_joke(self, joke: Joke) -> Joke:
        self.jokes.append(joke)
        return joke
```

This approach gives us both compile-time type checking with basedpyright and runtime safety through Python's ABC mechanism.

## Alternatives Considered

### Protocol Approach

```python
from typing import Protocol

class JokesRepositoryPort(Protocol):
    def get_jokes(self) -> list[Joke]: ...
    def create_joke(self, joke: Joke) -> Joke: ...

# Structural typing - no inheritance required
class InMemoryJokesRepository:
    def get_jokes(self) -> list[Joke]:
        return self.jokes
    
    def create_joke(self, joke: Joke) -> Joke:
        self.jokes.append(joke)
        return joke
```

**Rejected because**: Less explicit contracts, potentially confusing for team members, and weaker IDE support.

### Mixed Approach

Use Protocol for some interfaces and ABC for others based on context.

**Rejected because**: Increases cognitive load, creates inconsistency, and provides minimal benefit over single approach.