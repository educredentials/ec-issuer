# Credential Configuration

The EC Issuer CLI container includes a default credential configuration file at `/etc/openbadge_credential_configuration.json`. This file is sourced from `docs/src/openbadge_credential_configuration.json` and is automatically included in the CLI Docker image.

## Using the Configuration File

The configuration file can be used with the CLI to create or update credential configurations:

```bash
# Create a new credential configuration from the default file
ec-issuer-cli credential-configuration create my-config-id < /etc/openbadge_credential_configuration.json

# Update an existing credential configuration
ec-issuer-cli credential-configuration update my-config-id < /etc/openbadge_credential_configuration.json

# View the configuration
cat /etc/openbadge_credential_configuration.json
```

## Available CLI Commands

Run `ec-issuer-cli credential-configuration --help` for a complete list of commands:

```
Commands:
    create <id> - Create a new config (reads JSON from stdin)
    show <id>   - Show a credential configuration by ID
    update <id> - Update a config (reads JSON from stdin)
    list        - List all credential configurations
```
