FROM ghcr.io/depado/platypus:latest

WORKDIR /app

# Copy in the mock file
COPY ./ssi-agent-mock.yaml /app/mock.yaml

ENTRYPOINT ["/go/bin/platypus"]
