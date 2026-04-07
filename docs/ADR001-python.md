---
status: accepted
date: 2026-04-31 
deciders: Daniel Ostkamp, Thomas Kalverda, Bèr Kessels
consulted: See deciders
informed: See deciders
---
# ADR001: Python and Flask for service

After an intial PoC with rust, we decided to build the issuer service in Python, without any framework.

## Context and Problem Statement

[ADR-021 Issuer service](https://confluence.ia.surf.nl/spaces/EDUCRED/pages/296915119/ADR-021+Issuer+service)
> Wrap SSI-Agent and/or edci-issuer in own ec-issuer. Starting with SSI-Agent.

[ADR-009 Rust for Cryptographic Operations](https://confluence.ia.surf.nl/spaces/EDUCRED/pages/296915111/ADR-009+Rust+for+Cryptographic+Operations) and [ADR-005 Polyglot Microservices Strategy](https://confluence.ia.surf.nl/spaces/EDUCRED/pages/296915094/ADR-005+Polyglot+Microservices+Strategy)

> Core services: Python/Django (Credential, Organization, Identity)
> Signing service: Rust (Impierce-based) -
> Future services: Language appropriate to problem domain 

[ADR-004](https://confluence.ia.surf.nl/spaces/EDUCRED/pages/296915090/ADR-004+Adopt+Hexagonal+Architecture+Pattern) requires us to
implement ports and adapters. The storage (database) and HTTP (the API) are such adapters and must adhere to this pattern.

## Decision Drivers

* Future maintenance
* Available team and -knowledge

## Considered Options

* Rust
* Python

## Decision Outcome

Chosen option: "Python"

Since the signing service is in rust, and the issuer-service wraps this to add
our business-logic, API and other integrations, the issuer-service falls into
the "Core services" category.

We use the latest stable Python version at time of writing: 3.14.x.

Package-management, version management, linting, formatting, typechecking all go through the astral tools (uv, ruff, ty etc)

### Consequences

* Good: Python is well-known and has many developers avaiable to work on.
* Good: Boilerplate is minimal since Python is a high-order language, leaving e.g. memory management to the runtime.
* Neutral: Python performs poorly compared to rust, but since this service is not performance-critical, the extra cost is minimal.
* Bad: Runtime management-, building and setup requires additional, complex tooling like Containers to maintain parity and allow easy on-boarding.
* Bad: We must rely on external type-checking and linting to avoid many runtime bugs and errors that other languages avoid in compile-time.
* Bad: We must use a type-checker and implement interface contracts using `abc.ABC` to adhere to the "Interfaces" part of the Ports and Adapters Architecture. Python does not have native interface support.
* Bad: We must rely on external linting and type checking since Python does not have native tooling for this.
