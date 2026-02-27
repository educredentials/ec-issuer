# Use Python 3.10 slim as base image
FROM python:3.10-slim as builder

WORKDIR /app

# Install uv for dependency management
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --system --no-deps -r <(uv pip compile pyproject.toml)

# Runtime stage - Use Python 3.10 slim
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libssl3 ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /opt/venv

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/opt/venv/bin:$PATH"
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8080

# Expose the port the service runs on
EXPOSE 8080

# Run the application
CMD ["python", "src/main.py"]