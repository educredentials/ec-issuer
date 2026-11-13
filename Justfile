# Justfile for EC Issuer - Modern Make alternative
# Install: https://github.com/casey/just#readme

# Load environment variables from .env into the environment (for `just develop`)
set dotenv-load

# Default target
default:
    @just --list

# Detect container runtime (podman or docker)
runtime := `(command -v docker >/dev/null 2>&1 && echo docker || echo podman)`

# Start development server (Rust)
develop:
    {{runtime}} compose up --wait --wait-timeout 10 --detach postgresql mock-ssi-agent mock-oidc-auth mock-awards
    cargo run --bin ec-issuer-web

# (re)start all dependency services - everything except the ec-issuer
dependencies:
    {{runtime}} compose down
    {{runtime}} compose up --wait --wait-timeout 10 --detach postgresql mock-ssi-agent mock-oidc-auth mock-awards

# Run all quality checks (linting + type checking)
lint:
    cargo fmt --check
    cargo clippy -- -D warnings

# Run tests
test_pattern_default := 'tests/'

test test-pattern=test_pattern_default:
    cargo test -- --test-threads=1

# Run tests and only show failed or errors
test-rfe test-pattern=test_pattern_default:
    cargo test -- --test-threads=1 -rfE

# Run e2e services
e2eservices:
    {{runtime}} compose down
    {{runtime}} compose up --wait --wait-timeout 10 --detach ec-issuer-rust postgresql mock-ssi-agent mock-oidc-auth mock-awards

bump_value_default := 'minor'

# Bump version, create changelog and add this to the tag
release bump-value=bump_value_default:
    #!/usr/bin/env bash
    set -euo pipefail
    previous_version=$(grep '^version' Cargo.toml | cut -d'"' -f2)
    this_version=$(bash scripts/bump-version-cargo.sh {{bump-value}} | tail -1)
    git add Cargo.toml
    changelog=$(git log --pretty=format:'%s' "v${previous_version}".."HEAD")
    git commit -m "Bump version to ${this_version}"
    git tag -a "v${this_version}" -m "${changelog}"

# Run everything (lint + test)
all:
    just lint
    just e2eservices
    just test
