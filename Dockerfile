# Use Python 3.10 slim as base image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN uv venv --clear && \
    . .venv/bin/activate && \
    uv pip install --system --no-deps flask

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8080

# Expose the port the service runs on
EXPOSE 8080

# Run the application
CMD ["python", "src/main.py"]