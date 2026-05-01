FROM ghcr.io/depado/platypus:latest

WORKDIR /app

COPY ./ssi-agent-mock.yaml /app/mock.yaml

ENTRYPOINT ["/go/bin/platypus"]
