# Use cargo-chef for optimal caching
FROM lukemathwalker/cargo-chef:latest-rust-1 AS chef
WORKDIR /app

# Start with just a recipe for dependencies
FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

# Build dependencies
FROM chef AS builder
COPY --from=planner /app/recipe.json recipe.json
# Build only dependencies to cache them
RUN cargo chef cook --release --recipe-path recipe.json
# Now build application code
COPY . .
RUN cargo build --release

# Runtime stage - Use Debian bookworm which has libssl3
FROM debian:bookworm-slim
WORKDIR /app

# Install OpenSSL and CA certificates for HTTPS requests
RUN apt-get update && \
    apt-get install -y --no-install-recommends libssl3 ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the binary from the build stage
COPY --from=builder /app/target/release/ec-issuer /usr/local/bin/ec-issuer

# Set environment variables for the service
# By default, listen on all interfaces (0.0.0.0) for Docker
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8080

# Expose the port the service runs on
EXPOSE 8080

# Run the binary
CMD ["ec-issuer"]
