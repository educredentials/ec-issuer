# Credential Service - EC Issuer

Credential service that issues and signs **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

[![Python CI/CD](https://github.com/educredentials/ec-issuer/actions/workflows/python-ci.yml/badge.svg)](https://github.com/educredentials/ec-issuer/actions/workflows/python-ci.yml)

This service orchestrates and integrates with existing issuer services, working alongside them.

## Features

- **Issue Credentials**: Create and sign verifiable credentials
- **Multiple Formats**: Support for Open Badges 3.0 and European Learner Model
- **Revocation**: Revoke credentials with reason tracking
- **Expiration**: Automatic status updates for expired credentials
- **Digital Signatures**: Integration with signing service

## Technology Stack

- **Flask**: Lightweight HTTP server
- **UV, Ruff, Basedpyright**: Runtime, dependency manager, linter, typechecker
- **Pytest**: Run tests
- **Docker or Podman**: Building containers, running (mocks of) external services 
- **Github Actions**: Test, Lint, Typecheck, Build and push images

## Goals

- Simple, pragmatic REST API for credential administration: issue, aka create-offers
- Authorization of issuing actor (may they issue achievement to user?)
- Validation of data model and prerequisites 
- Orchestrating the credential creation workflow
- Publishing events for downstream processing
- Signing and delivering OpenBadges 3.0 credentials to wallets via OID4VCI
- Signing and delivering ELM credentials as downloadable credential files

### Out of scope? Unknown if still relevant

- Batching operations for efficient signing
- Embedding resources (images, evidence) or their resource-integrity hashes in credentials
- Multitenancy, depends on our criteria around signing -on-behalf-of-, but could be implemented with a dedicated issuer-agent issuer per tenant

## Non Goals

- Revocation. Part of ec-status.
- BadgeClass (template, achievements) management. Part of ec-achievement.
- Authorization logic. Part of ec-authorization.
- Key management. Part of ec-key.
- Trust anchoring. Part of ec-trust and/or ec-key.
- Notifications and messaging (emails, push notifications etc). Part of ec-notifications.
- Storage of claims, users, credentials. Part of resp ec-achievement, ec-user, ec-award(locker).

## Getting Started

### Prerequisites

- Python 3.10+
- UV
- Podman (for running tests that require services)

### Environment Variables

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
SSI_AGENT_URL="https://issuer.example.com"
SSI_AGENT_NONCE_ENDPOINT="https://issuer.example.com/openid4vci/nonce"
SSI_AGENT_CREDENTIAL_ENDPOINT="https://issuer.example.com/openid4vci/credential"
```

### Running the Service

```bash
just develop
```

The service will start on `http://localhost:8080`

### Running Tests

```bash
just test        # Run unit and integration tests
```

**Note:** Integration and e2e tests require external services to be running. e2e tests require the service to be running as well.

To start services for testing:
```bash
just dependencies
```

The CI pipeline provides required services via GitHub Actions. Locally, you must start services before running tests that require them. Test fixtures never start or stop services — they only return connection strings.

## Development

This project uses [Just](https://github.com/casey/just) for common development tasks and has a GitHub Actions CI/CD pipeline.

## Testing

This project follows the [Testing Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) approach with three test levels:

- **Unit tests**: Fast, isolated tests of individual components using test doubles
- **Integration tests**: Tests that verify interactions between components, may require external services
- **End-to-end tests**: Tests that verify complete system behavior through the public API

### Available Commands

Run `just --list` for all commands, including starting services, linting, running tests, building and so on.

## Deployment

### Version

We use semantic versioning. 

Bump version with `uv version --bump`, see `uv version --help` for all options.
On git branch `main`, add a git tag with the same version, with `git tag --sign "v$(uv version --short)"`. Add a short message with the main change.
Push main branch to github. The CI/CD will build a container after all checks and tests pass. 

Deploying this container is not automated yet, due to limitations of the hosting environment (Surf Development Platform, SDP).
Management of this platform, and therefore deployment, is done via [a separate infrastructure repository](https://git.ia.surfsara.nl/surf-internal/educational-logistics/edubadges/educredentials/).

## License

MIT
