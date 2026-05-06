# Justfile for EC Issuer - Modern Make alternative
# Install: https://github.com/casey/just#readme

# Annoying "tip" that flask prints, but we cannot and should not implement
export FLASK_SKIP_DOTENV := "true"

# Default target
default:
    @just --list

# Detect container runtime (podman or docker)
runtime := `(command -v podman >/dev/null 2>&1 && echo podman || echo docker)`

# Start development server
develop:
    uv run python -m src.main

# (re)start all dependency services - everything except the ec-issuer
dependencies:
    {{runtime}} compose down
    {{runtime}} compose --profile real-ssi-agent up --detach --abort-on-container-exit postgresql mock-ssi-agent real-ssi-agent

# Run all quality checks (linting + type checking)
lint:
    uv run ruff check .
    uv run basedpyright .

test_pattern_default := 'tests/'

# Run tests
test test-pattern=test_pattern_default:
    uv run pytest {{test-pattern}} -v

# Generate Python code documentation with pdoc
docs-code:
    uv sync
    uv run pdoc -o docs/book/pydoc src/

# Run mdbook to preview the docs. See https://rust-lang.github.io/mdBook/
docs:
    mdbook serve docs

# Run everything (lint + test)
all:
    just lint
    just test
