# Credential Service - Flask-based EC Issuer

Flask-based credential service that issues and signs **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

## Features

- **Issue Credentials**: Create and sign verifiable credentials
- **Multiple Formats**: Support for Open Badges 3.0 and European Learner Model
- **Revocation**: Revoke credentials with reason tracking
- **Expiration**: Automatic status updates for expired credentials
- **Digital Signatures**: Integration with signing service
- **REST API**: Clean HTTP API with Flask
- **Type Safety**: Python type annotations for correctness

## Technology Stack

- **Flask**: Lightweight HTTP server
- **SQLAlchemy**: ORM for database interactions
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production
- **Python 3.10+**: Modern Python features

## Getting Started

### Prerequisites

- Python 3.10+
- UV (for dependency management)
- PostgreSQL 14+ (for production)
- SQLite (for development)

### Environment Variables

```bash
# Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# Database configuration (SQLite for development)
DATABASE_URL=sqlite:///credentials.db

# Signing service configuration
SIGNING_USE_GRPC=false
SIGNING_SERVICE_URL=http://localhost:50051
```

### Running the Service

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Run the application
flask run --host=0.0.0.0 --port=8080
```

The service will start on `http://localhost:8080`

### Running Tests

```bash
# Install test dependencies
uv pip install pytest requests

# Run tests
pytest tests/
```

## Development

This project uses [Just](https://github.com/casey/just) for common development tasks.

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
- [ ] Configuration management
- [ ] Database integration

### Milestone 2: Credential Issuance
- [ ] Create credential endpoint
- [ ] Signing service integration
- [ ] Open Badges 3.0 support
- [ ] European Learner Model support

### Milestone 3: Production Readiness
- [ ] Authentication and authorization
- [ ] Logging and monitoring
- [ ] CI/CD pipeline
- [ ] Documentation

## License

MIT