# OIDC4VCI Issuer Agent

The OIDC4VCI issuer agent handles the OpenID for Verifiable Credentials Issuance (OIDC4VCI) flow. It works alongside the EC-issuer service to manage credential offers and issuance. The current implementation uses _unime core_, aka _ssi-agent_ from Impierce.

## Overview

The OIDC4VCI issuer agent is responsible for:

1. Handling the OIDC4VCI flow with wallets
2. Handling the authentication check on issuance with the OIDC4VCI Authorization Code Flow

## Architecture

The agent follows the architecture decision outlined in [ADR003: Expose ssi-agent as peer service alongside ec-issuer](./adr/ADR003-ssi-agent-as-peer-service.md).

## Integration with EC-issuer

The EC-issuer service (this service) controls the OIDC4VCI issuer agent by:

1. Managing offers, credentials, and credential configurations
2. Handing the offer over to a wallet which directly interacts with the agent
3. Ingesting any events from the OIDC4VCI issuer agent and publishing that in our generic event system `ec-notifications`

For more details on the integration process, see the [Import in Wallet](./import_in_wallet.md) documentation.

## Key Responsibilities

The OIDC4VCI issuer agent's key responsibilities include:

- Creating OIDC4VCI credential offers on request from `ec-issuer`
- Sending and/or showing this offer to a user
- Querying the status of the offer
- Providing an event endpoint where OIDC4VCI issuer agent can deliver its events for future integration with our event-bus and audit-trail

## Implementation Details

The agent is implemented using the Unime ssi-agent, which follows the [Unime ssi-agent integration guidelines](https://beta.docs.impierce.com/unicore/integration/use-cases/issue-a-credential).

The software is based on the [Impierce SSI-Agent](https://github.com/impierce/ssi-agent), and our specific build is maintained in the [educredentials ssi-agent-build repository](https://github.com/educredentials/ssi-agent-build).

For more information on the implementation and architecture decisions, refer to [ADR003: Expose ssi-agent as peer service alongside ec-issuer](./adr/ADR003-ssi-agent-as-peer-service.md).
