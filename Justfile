# Justfile for EC Issuer - Modern Make alternative
# Install: https://github.com/casey/just#readme

# Annoying "tip" that flask prints, but we cannot and should not implement
export FLASK_SKIP_DOTENV := "true"

# Default target
default:
    @just --list

# Detect container runtime (podman or docker)
runtime := `(command -v docker >/dev/null 2>&1 && echo docker || echo podman)`

# Start development server
develop:
    uv run ec-issuer-web

# (re)start all dependency services - everything except the ec-issuer
dependencies:
    {{runtime}} compose down
    {{runtime}} compose up --wait --wait-timeout 10 --detach postgresql mock-ssi-agent mock-oidc-auth mock-awards

e2eservices:
    {{runtime}} compose down
    {{runtime}} compose up --wait --wait-timeout 10 --detach ec-issuer postgresql mock-ssi-agent mock-oidc-auth mock-awards

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

bump_value_default := 'minor'

# Bump version, create changelog and add this to the tag
release bump-value=bump_value_default:
    #!/usr/bin/env bash
    set -euo pipefail
    previous_version=$(uv version --short)
    this_version=$(uv version --bump {{bump-value}} --short)
    changelog=$(git log --pretty=format:'%s' "${previous_version}".."${this_version}")
    git tag -a "${this_version}" -m "${changelog}"

# Run everything (lint + test)
all:
    just lint
    just e2eservices
    just test
