# Justfile for EC Issuer - Modern Make alternative
# Install: https://github.com/casey/just#readme

# Annoying "tip" that flask prints, but we cannot and should not implement
export FLASK_SKIP_DOTENV := "true"

# Default target
default:
    @just --list

# Start development server
develop:
    uv run python -m src.main

# Run all quality checks (linting + type checking)
lint:
    uv run ruff check .
    uv run basedpyright check .

# Run all tests
test:
    uv run pytest tests/ -v

# Run only unit tests
test-unit:
    uv run pytest tests/unit/ -v

# Run only e2e tests
test-e2e:
    uv run pytest tests/e2e/ -v

# Run everything (lint + test)
all:
    just lint
    just test
