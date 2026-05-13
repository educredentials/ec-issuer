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

# Generate OpenAPI documentation with Redoc
docs-api:
    mkdir -p docs/book/openapi
    cp docs/api/openapi.yaml docs/book/openapi/openapi.yaml
    cp docs/api/index.html docs/book/openapi/index.html

# Run mdbook to preview the docs. See https://rust-lang.github.io/mdBook/
docs:
    mdbook serve docs

# Seed the database with credential issuer metadata from a JSON file
update-issuer-metadata file:
    uv run python -m src.sysadmin.commandline_adapter update-issuer-metadata < {{file}}

# Run everything (lint + test)
all:
    just lint
    just dependencies
    just develop &
    just test
