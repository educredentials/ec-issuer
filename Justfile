# Justfile for EC Issuer - Modern Make alternative
# Install: https://github.com/casey/just#readme

# Annoying "tip" that flask prints, but we cannot and should not implement
export FLASK_SKIP_DOTENV := "true"

# Default target
default:
    @just --list

# Start development server
# Metrics are default disabled in dev mode. ENV enables it, but makes dev slower
develop $DEBUG_METRICS="1":
    uv run python -m src.main

# Run all quality checks (linting + type checking)
lint:
    uv run ruff check .
    uv run basedpyright .

# Run all tests
test:
    uv run pytest tests/ -v

# Run only unit tests
test-unit:
    uv run pytest tests/unit/ -v

# Run only integration tests
test-integration:
    uv run pytest tests/integration/ -v

# Run only e2e tests
test-e2e:
    uv run pytest tests/e2e/ -v

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
