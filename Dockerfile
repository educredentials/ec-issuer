FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1
# Install managed Python to a fixed path so we can copy it predictably to the final image
ENV UV_PYTHON_INSTALL_DIR=/python

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --python 3.14
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --python 3.14

# Distroless: no shell, no package manager, no pip — glibc, libssl, zlib, ca-certs only
FROM gcr.io/distroless/base-debian12

# uv's managed Python (python-build-standalone) statically links OpenSSL and
# sqlite3, so those do not appear as system packages and won't produce CVEs here
COPY --from=builder /python /python
# psycopg2-binary bundles its own libpq/ssl/krb5 but still links against system zlib
COPY --from=builder /usr/lib/x86_64-linux-gnu/libz.so.1 /usr/lib/x86_64-linux-gnu/libz.so.1
COPY --from=builder --chown=65532:65532 /app/.venv /app/.venv
COPY --chown=65532:65532 src/ /app/src/

# nonroot is UID 65532 in all distroless images
USER nonroot

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONPATH="/app/src"
CMD ["python", "-m", "src.main"]
