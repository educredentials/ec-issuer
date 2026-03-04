# Credential Service - Flask-based EC Issuer

Flask-based credential service that issues and signs **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

[![Python CI/CD](https://github.com/educredentials/ec-issuer/actions/workflows/python-ci.yml/badge.svg)](https://github.com/educredentials/ec-issuer/actions/workflows/python-ci.yml)

## Features

- **Issue Credentials**: Create and sign verifiable credentials
- **Multiple Formats**: Support for Open Badges 3.0 and European Learner Model
- **Revocation**: Revoke credentials with reason tracking
- **Expiration**: Automatic status updates for expired credentials
- **Digital Signatures**: Integration with signing service

## Technology Stack

- **Flask**: Lightweight HTTP server
- **UV, Ruff, TY**: Runtime, dependency manager, linter, typechecker
- **Pytest**: Run tests
- **Docker or Podman**: Building and running images
- **Github Actions**: Test, Lint, Typecheck, Build and push images

## Getting Startede

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

## Roadmap

### Milestone 1: Basic Flask Setup
- [x] Flask application structure
- [x] Health endpoint
- [x] Basic testing setup
- [x] Configuration management
- [x] CI/CD pipeline

### Milestone 2: Credential Issuance
- [ ] Create credential endpoint (Issue credential)
- [ ] Open Badges 3.0 support
- [ ] European Learner Model support
- [ ] Statuslist support
- [ ] Create credential with metadata (Cijfer, Persoonlijke Boodschap, Naam, Beschrijving)
- [ ] Create Credential with evidence metadata (Evidence URL)

### Milestone 3: Authorization Code Flow
- [ ] Implement full OIDC4VCI flow for OBv3.0
- [ ] Use, link or mock an openid service that supports OIDC4VCI and wraps surfconext
- [ ] On return, callback to "achievement" endpoint to fetch the final achievement

### Milestone 4: Signing
- [ ] Signing service integration
- [ ] eseal signature support

## License

MIT
