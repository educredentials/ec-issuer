# Credential Service - EC Issuer

Credential service that issues and signs **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

[![Python CI/CD](https://github.com/educredentials/ec-issuer/actions/workflows/python-ci.yml/badge.svg)](https://github.com/educredentials/ec-issuer/actions/workflows/python-ci.yml)

This service wraps and abstracts existing issuance services.

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
- **Docker or Podman**: Building and running images
- **Github Actions**: Test, Lint, Typecheck, Build and push images
- **CLI VC Wallet**: At `tests/e2e/cli-vc-wallet`, built from [cli-vc-wallet](https://github.com/educredentials/cli-vc-wallet)

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

### Environment Variables

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
ISSUER_AGENT_BASE_URL="https://issuer.example.com"
```

### Running the Service

```bash
just develop
```

The service will start on `http://localhost:8080`

### Running Tests

```bash
just test
```

## Development

This project uses [Just](https://github.com/casey/just) for common development tasks and has a GitHub Actions CI/CD pipeline.

### Project Structure

```
src/
├── main.py          # Flask application entry point
├── config.py        # Configuration management
├── models.py        # Database models
├── routes/          # API routes
└── services/        # Business logic

tests/
├── e2e/            # End-to-end tests
└── unit/           # Unit tests
```

### Available Commands

```bash
# Start development server
just develop

# Run quality checks (linting + type checking)
just lint

# Run tests
just test        # All tests
just test-unit   # Only unit tests
just test-e2e    # Only e2e tests

# Run everything
just all
```

### Adding a New Endpoint

1. Create a new route in `src/routes/`
2. Add the route to the Flask app in `src/main.py`
3. Write tests in `tests/`
4. Implement the business logic in `src/services/`

## Docker

Build and run the service using Docker:

```bash
docker build -t ec-issuer .
docker run -p 8080:8080 ec-issuer
```

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
