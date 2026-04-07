"""
Jokes App using Hexagonal Architecture with Python ABC

This implementation demonstrates Hexagonal Architecture (Ports and Adapters pattern)
using Python's ABC module for interface enforcement and type safety.

Terminology:
- Inbound Ports: Interfaces for driving the application (user interaction)
- Outbound Ports: Interfaces for infrastructure needs (persistence, etc.)
- Inbound Adapters: Concrete implementations of inbound ports (CLI, web, etc.)
- Outbound Adapters: Concrete implementations of outbound ports (repositories, etc.)
"""

import json
import sys
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypedDict, override


def main() -> None:
    """Main entry point that parses command-line arguments and executes commands."""
    if len(sys.argv) < 2:
        print("Usage: python ports_adapters.py <command> [args...]")
        print("Commands:")
        print("  list          - List all jokes")
        print("  create <joke> - Create a new joke")
        print("  update <id> <joke> - Update a joke")
        return

    command = sys.argv[1]
    joke_repository = FileStorageRepository()
    joke_service = JokeService(joke_repository)
    jokes_interaction = CommandlineJokesInteraction(joke_service)

    if command == "list":
        jokes_interaction.list_jokes()
    elif command == "create" and len(sys.argv) > 2:
        joke_content = " ".join(sys.argv[2:])
        _ = jokes_interaction.create_joke(joke_content)
    elif command == "update" and len(sys.argv) > 3:
        joke_id = sys.argv[2]
        joke_content = " ".join(sys.argv[3:])
        _ = jokes_interaction.update_joke(joke_id, joke_content)
    else:
        print(f"Unknown command or missing arguments: {sys.argv[1:]}")
        print("Use 'python ports_adapters.py' for usage.")


class Joke:
    """
    Domain model with business logic for parsing joke content.

    Uses ABC-style interface enforcement through type hints and runtime validation.
    The from_content method enforces business rules about joke structure.
    """

    id: str
    title: str
    body: str

    @classmethod
    def from_content(cls, content: str) -> "Joke":
        """
        Business rule: Jokes must have title/body separated by punctuation.

        This enforces the domain constraint that jokes follow a specific format.
        The explicit type annotations enable static type checking of this contract.

        Format: "Title. Body content" or "Title? Body content"
        - Title: Text including the first punctuation (period or question mark)
        - Body: Text after the first punctuation
        """

        id = str(uuid.uuid4())

        # Find the first occurrence of either period or question mark
        period_pos = content.find(".")
        question_pos = content.find("?")

        # Determine which punctuation comes first
        if period_pos == -1 and question_pos == -1:
            raise ValueError("Invalid joke. Did you add a period or question mark?")

        # Use the first punctuation found
        if period_pos != -1 and (question_pos == -1 or period_pos < question_pos):
            split_pos = period_pos
            # Title includes punctuation, body is text after
            title = content[: split_pos + 1].strip()
            body = content[split_pos + 1 :].strip()
        else:
            split_pos = question_pos
            # Title includes punctuation, body is text after
            title = content[: split_pos + 1].strip()
            body = content[split_pos + 1 :].strip()

        # Handle empty body case
        if not body:
            raise ValueError("Invalid joke format: missing body after punctuation")

        return cls(id, title, body)

    def __init__(self, id: str, title: str, body: str) -> None:
        self.id = id
        self.title = title
        self.body = body

    @override
    def __repr__(self) -> str:
        return f"Joke(id={self.id}, title={self.title}, body={self.body})"

    @override
    def __str__(self) -> str:
        return f"{self.title}\n{self.body}"


class JokeService:
    """
    Application service that coordinates domain logic using dependency injection.

    Depends on JokesRepositoryPort (interface) not concrete implementations.
    This enables static type checking of dependencies while allowing runtime
    flexibility to swap implementations (e.g., InMemory vs Hardcoded repositories).
    """

    joke_repository: "JokesRepositoryPort"

    def __init__(self, joke_repository: "JokesRepositoryPort") -> None:
        self.joke_repository = joke_repository

    def run(self) -> None: ...

    def get_jokes(self) -> list[Joke]:
        return self.joke_repository.get_jokes()

    def create_joke(self, content: str) -> Joke:
        joke = Joke.from_content(content)
        return self.joke_repository.create_joke(joke)

    def update_joke(self, id: str, content: str) -> Joke:
        joke = Joke.from_content(content)
        joke.id = id
        return self.joke_repository.update_joke(joke)


class JokesInterationPort(ABC):
    """
    Inbound Port: Interface for driving the application via user interaction.

    This inbound port defines how external actors (users) interact with the application.
    ABC (Abstract Base Class) enforces that inbound adapters implement all methods.
    Type checkers catch missing implementations at development time.
    """

    @abstractmethod
    def run(self) -> None: ...

    @abstractmethod
    def get_jokes(self) -> list[Joke]: ...

    @abstractmethod
    def create_joke(self, content: str) -> Joke: ...

    @abstractmethod
    def update_joke(self, id: str, content: str) -> Joke: ...


class CommandlineJokesInteraction(JokesInterationPort):
    """
    Inbound Adapter: CLI implementation of the inbound port.

    This inbound adapter implements the JokesInterationPort contract using
    command-line arguments instead of interactive input. This makes it more
    suitable for testing and automation while still satisfying the ABC interface.
    """

    joke_service: JokeService

    def __init__(self, joke_service: JokeService):
        self.joke_service = joke_service

    @override
    def run(self) -> None:
        """Run the CLI application. Called by main() with parsed arguments."""
        # This method is called by main() after parsing arguments
        # The actual command execution is handled by individual methods
        pass

    def list_jokes(self) -> None:
        """List all jokes - implements 'list' command"""
        jokes = self.get_jokes()
        if not jokes:
            print("No jokes found.")
            return

        print(f"Found {len(jokes)} joke(s):")
        for i, joke in enumerate(jokes, 1):
            print(f"{i}. {joke}")

    @override
    def create_joke(self, content: str) -> Joke:
        """Create a new joke - implements 'create' command"""
        try:
            joke = self.joke_service.create_joke(content)
            print(f"Created joke: {joke}")
            return joke
        except ValueError as e:
            print(f"Error creating joke: {e}")
            exit(1)

    @override
    def update_joke(self, id: str, content: str) -> Joke:
        """Update a joke - implements 'update' command"""
        try:
            joke = self.joke_service.update_joke(id, content)
            print(f"Updated joke: {joke}")
            return joke
        except Exception as e:
            print(f"Error updating joke: {e}")
            exit(1)

    @override
    def get_jokes(self) -> list[Joke]:
        """Get all jokes from service layer"""
        return self.joke_service.get_jokes()


class JokesRepositoryPort(ABC):
    """
    Outbound Port: Interface for infrastructure persistence operations.

    Defines contract for persistence. ABC ensures adapters implement all methods.
    Enables type-safe DI in JokeService. Domain depends on interface only.
    """

    @abstractmethod
    def get_jokes(self) -> list[Joke]: ...

    @abstractmethod
    def create_joke(self, joke: Joke) -> Joke: ...

    @abstractmethod
    def update_joke(self, joke: Joke) -> Joke: ...


class InMemoryJokesRepository(JokesRepositoryPort):
    """
    Outbound Adapter: In-memory implementation of the outbound port.

    Satisfies JokesRepositoryPort contract using in-memory storage. Can be swapped with
    other implementations without changing JokeService or domain logic.
    """

    jokes: list[Joke]

    def __init__(self) -> None:
        self.jokes = []

    @override
    def get_jokes(self) -> list[Joke]:
        return self.jokes

    @override
    def create_joke(self, joke: Joke) -> Joke:
        self.jokes.append(joke)
        return joke

    @override
    def update_joke(self, joke: Joke) -> Joke:
        for i, j in enumerate(self.jokes):
            if j.id == joke.id:
                self.jokes[i] = joke
                return joke
        raise StorageError("Joke not found")


class JokeData(TypedDict):
    id: str
    title: str
    body: str


class FileStorageRepository(JokesRepositoryPort):
    """
    Outbound Adapter: File-based implementation of the outbound port.

    Persists jokes as JSON files in a temporary directory. This provides
    real persistence across command executions, enabling proper end-to-end testing.
    """

    def __init__(self, storage_dir: str = "/tmp/jokes_db") -> None:
        self.storage_dir: Path = Path(storage_dir)

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(exist_ok=True)

    def _get_joke_path(self, joke_id: str):
        """Get the file path for a joke"""
        return self.storage_dir / f"{joke_id}.json"

    def _read_joke(self, joke_id: str) -> Joke:
        """Read a joke from file"""
        joke_path = self._get_joke_path(joke_id)
        if not joke_path.exists():
            raise StorageError(f"Joke {joke_id} not found")

        with open(joke_path, "r") as f:
            data: JokeData = json.load(f)  # pyright: ignore[reportAny] We don't want to override json.load's type

        return Joke(id=data["id"], title=data["title"], body=data["body"])

    def _write_joke(self, joke: Joke) -> None:
        """Write a joke to file"""
        joke_path = self._get_joke_path(joke.id)
        data = {"id": joke.id, "title": joke.title, "body": joke.body}

        with open(joke_path, "w") as f:
            json.dump(data, f, indent=2)

    def _delete_joke(self, joke_id: str) -> None:
        """Delete a joke file"""
        joke_path = self._get_joke_path(joke_id)
        if joke_path.exists():
            joke_path.unlink()

    @override
    def get_jokes(self) -> list[Joke]:
        """Get all jokes from file storage"""
        if not self.storage_dir.exists():
            return []

        jokes: list[Joke] = []
        for json_file in self.storage_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data: JokeData = json.load(f)  # pyright: ignore[reportAny] We don't want to override json
                joke = Joke(id=data["id"], title=data["title"], body=data["body"])
                jokes.append(joke)
            except (json.JSONDecodeError, KeyError, IOError):
                # Skip corrupted files
                continue

        return jokes

    @override
    def create_joke(self, joke: Joke) -> Joke:
        """Create a new joke in file storage"""
        self._write_joke(joke)
        return joke

    @override
    def update_joke(self, joke: Joke) -> Joke:
        """Update a joke in file storage"""
        if not self._get_joke_path(joke.id).exists():
            raise StorageError(f"Joke {joke.id} not found")

        self._write_joke(joke)
        return joke


class StorageError(Exception):
    pass


if __name__ == "__main__":
    main()
