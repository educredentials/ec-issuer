# Justfile for EC Issuer - Modern Make alternative
# Install: https://github.com/casey/just#readme

# Default target
default:
    @just --list

# Start development server
develop:
    @echo "🚀 Starting development server..."
    python -m src.main

# Run all quality checks (linting + type checking)
lint:
    @echo "🔍 Running quality checks..."
    ruff check .
    mypy .
    @echo "✅ All quality checks passed!"

# Run all tests
test:
    @echo "🧪 Running all tests..."
    pytest tests/ -v

# Run only unit tests
test-unit:
    @echo "🧪 Running unit tests..."
    pytest tests/unit/ -v

# Run only e2e tests
test-e2e:
    @echo "🧪 Running e2e tests..."
    pytest tests/e2e/ -v

# Run everything (lint + test)
all:
    @echo "🔥 Running full quality suite..."
    just lint
    just test
    @echo "🎉 All checks passed!"