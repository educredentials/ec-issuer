# Deep Modules

From "A Philosophy of Software Design":

**Deep module** = small interface + lots of implementation

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid)

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing interfaces, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Python: Interfaces and Privacy

Python has no `interface` keyword and no access modifiers. We use two conventions to enforce deep module design:

**`ABC` as interface.** Define the public surface of a module as an `ABC` with `@abstractmethod`. Callers depend on the ABC, not the concrete class. This is how Ports are defined.

```python
from abc import ABC, abstractmethod

class JokesRepositoryPort(ABC):
    """Public interface: two methods, simple params."""

    @abstractmethod
    def get_jokes(self) -> list[Joke]: ...

    @abstractmethod
    def create_joke(self, joke: Joke) -> Joke: ...
```

**`_underscore` as private.** Everything that is not part of the public interface gets a `_` prefix. Ruff and basedpyright treat `_` names as internal and warn on external access. Keep the complex logic in `_` helpers; keep the public surface small.

```python
class FileStorageRepository(JokesRepositoryPort):
    """Deep implementation: rich logic hidden behind _ helpers."""

    def get_jokes(self) -> list[Joke]:
        return [self._read_joke(p) for p in self._storage_dir.glob("*.json")]

    def create_joke(self, joke: Joke) -> Joke:
        self._write_joke(joke)
        return joke

    def _read_joke(self, path: Path) -> Joke:
        ...  # file I/O, parsing, error handling

    def _write_joke(self, joke: Joke) -> None:
        ...  # serialisation, atomic write
```

The public interface is two methods. All the complexity is hidden. Tests only call `get_jokes` and `create_joke`.

## Module Structure

In this project, a **module** is a directory with an `__init__.py`. Modules are **one level deep** — no modules inside modules.

```
src/
  issuer_agent/       ← module
    __init__.py
    ssi_agent_adapter.py
  metadata/           ← module
    __init__.py
    metadata_repository.py
    postgresql_adapter.py
```

Each module exposes its public API through `__init__.py`. Internal files within a module are implementation details — they may use `_` prefixed names freely. Do not create sub-modules (a directory inside a module directory).
