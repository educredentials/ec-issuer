# Credential Configuration

The EC Issuer CLI container includes a default credential template file at `/etc/openbadge_credential_template.json`. This file is sourced from `templates/openbadge_credential_template.json` and is automatically included in the CLI Docker image. Additionally, during start-up of EC Issuer, the template is also loaded and created within VC-service.

## Using the Configuration File

The configuration file can be used with the CLI to create or update credential configurations:

```bash
# Create a new credential configuration from the default file
ec-issuer-cli credential-configuration create my-config-id < /etc/openbadge_credential_template.json

# Update an existing credential configuration
ec-issuer-cli credential-configuration update my-config-id < /etc/openbadge_credential_template.json

# View the configuration
cat /etc/openbadge_credential_template.json
```

## Available CLI Commands

Run `ec-issuer-cli credential-configuration --help` for a complete list of commands:

```
Commands:
    create <id> - Create a new template (reads JSON from stdin)
    show <id>   - Show a credential template by ID
    update <id> - Update a config (reads JSON from stdin)
    delete <id> - Deletes a template by ID
    list        - List all credential templates
```
