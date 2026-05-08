# ADR003: Expose ssi-agent as peer service alongside ec-issuer

| | |
|---|---|
| Status | accepted |
| Date | 2025-05-08 |
| Deciders | Daniel Ostkamp, Bèr Kessels |
| Consulted | See deciders |
| Informed | See deciders |

## Context and Problem Statement

The ec-issuer service was designed to wrap Unime's ssi-agent completely, hiding it behind a proxy layer. This approach has proven difficult in practice due to how the ssi-agent operates, particularly with the OID4VCI (OpenID for Verifiable Credentials Issuance) flow.

Attempting to proxy all ssi-agent functionality through ec-issuer requires significant workarounds in the proxy layer to make ec-issuer appear as the publisher. This means ec-issuer ends up re-implementing functionality that the ssi-agent already provides, creating unnecessary duplication and complexity.

The OID4VCI flow, in particular, is designed to work directly with the credential issuer's endpoints. By placing ssi-agent behind ec-issuer, we fight against this design rather than leveraging it.

## Decision Drivers

* Reduce complexity and maintenance burden
* Leverage ssi-agent's built-in OID4VCI functionality
* Follow Unime's integration guidelines
* Minimize duplicate functionality between services
* Maintain clear separation of concerns

## Considered Options

* **Option 1: Continue wrapping ssi-agent behind ec-issuer** - Maintain the current architecture where all ssi-agent endpoints are proxied through ec-issuer
* **Option 2: Expose ssi-agent as peer service next to ec-issuer** - Allow direct public access to specific ssi-agent paths, with ec-issuer handling only its own responsibilities

## Decision Outcome

Chosen option: "Expose ssi-agent as peer service next to ec-issuer", because this approach aligns with the ssi-agent's design and Unime's integration guidelines, eliminates the need for proxy workarounds, and reduces duplicate functionality.

Following the [Unime ssi-agent integration guidelines](https://beta.docs.impierce.com/unicore/integration/use-cases/issue-a-credential), ec-issuer will no longer handle the OID4VCI flow directly. Instead, it will manage the credential issuance lifecycle at a higher level.

### Consequences

* Good, because ec-issuer no longer needs complex proxy logic to hide ssi-agent
* Good, because we leverage ssi-agent's native OID4VCI support
* Good, because reduced code complexity and maintenance burden
* Good, because clearer separation of concerns between services
* Neutral, because ec-issuer's role shifts from direct flow handler to orchestration service
* Bad, because ssi-agent endpoints are directly exposed, requiring proper security configuration
* Bad, because API gateway configuration becomes slightly more complex with two services to manage

## Pros and Cons of the Options

### Option 1: Continue wrapping ssi-agent behind ec-issuer

* Bad, because requires complex proxy workarounds for OID4VCI flow
* Bad, because duplicates functionality already provided by ssi-agent
* Bad, because fights against ssi-agent's designed integration patterns
* Bad, because increases maintenance burden and complexity
* Good, because single entry point for all credential-related operations

### Option 2: Expose ssi-agent as peer service next to ec-issuer

* Good, because aligns with ssi-agent's architecture and Unime's guidelines
* Good, because eliminates proxy workarounds and hacking
* Good, because reduces duplicate code and maintenance
* Good, because clearer separation: ssi-agent handles OID4VCI, ec-issuer handles business logic
* Neutral, because requires public exposure of `.well-known/` and `openid4vci/` paths
* Bad, because two services instead of one for clients to interact with

## Implementation Details

Under this architecture:

* Public access is allowed to all `.well-known/` and `openid4vci/` paths of the ssi-agent
* All other ssi-agent paths remain internal or are disabled in the API gateway
* ec-issuer's responsibilities are:
  * Manage templates on the ssi-agent
  * Manage credential configurations on the ssi-agent
  * Create credentials by providing user-data and template-id to the ssi-agent
  * Create an offer on the ssi-agent
  * Send and/or show this offer to a user
  * Query the status of the offer
  * Provide an event endpoint where ssi-agent can deliver its events for future integration with our event-bus and audit-trail

## More Information

* [Unime ssi-agent Integration Guidelines - Issue a Credential](https://beta.docs.impierce.com/unicore/integration/use-cases/issue-a-credential)
