# Configuration

The EC Issuer is configured exclusively through environment variables, following the [12-factor app](https://12factor.net/config) methodology. All environment variables are mandatory — there are no fallbacks or magic defaults.

## Loading Environment Variables

The application does not read `.env` files directly. Use your preferred tool to load environment variables:

- [uv with --env-file](https://docs.astral.sh/uv/concepts/configuration-files/#environment-variable-files)
- [direnv](https://direnv.net/)
- Or any .env loader from [github.com/topics/dotenv](https://github.com/topics/dotenv)

The `.env.example` file in the repository root provides a template. Copy it to `.env` (which is gitignored) and modify as needed.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SERVER_HOST` | Host address to bind the server to |
| `SERVER_PORT` | Port to listen on |
| `PUBLIC_URL` | The URL on which the service is publicly available |
| `SSI_AGENT_URL` | The base URL of the SSI agent |
| `SSI_AGENT_NONCE_ENDPOINT` | Full URL to the SSI agent's nonce endpoint |
| `SSI_AGENT_CREDENTIAL_ENDPOINT` | Full URL to the SSI agent's credential endpoint |
| `POSTGRES_CONNECTION_STRING` | PostgreSQL connection string (format: `postgresql://user:password@host:port/database`) |
| `DEBUG_METRICS` | Enable `/metrics` endpoint (for development) |

## SSI Agent Endpoint Configuration

For standard OpenID4VCI-compliant agents, the nonce and credential endpoints are published in their Issuer Metdata.

To discover the correct endpoints from a running SSI agent, fetch its metadata:

```bash
curl -s https://agent.example.com/.well-known/openid-credential-issuer | jq -r '
  "SSI_AGENT_NONCE_ENDPOINT=$(.nonce_endpoint)\nSSI_AGENT_CREDENTIAL_ENDPOINT=$(.credential_endpoint)"
'
```

This outputs the exact values to use for `SSI_AGENT_NONCE_ENDPOINT` and `SSI_AGENT_CREDENTIAL_ENDPOINT`.

E.g. for ssi-agent, the endpoints are 
```
https://ssi-agent.example.com/openid4vci/nonce
https://ssi-agent.example.com/openid4vci/credential
```
