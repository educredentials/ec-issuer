# Support European Digital Credential (EDC) alongside Open Badges v3

| | |
| --- | --- |
| Status | proposed |
| Date | 2025-07-14 |
| Deciders | Engineering Team |
| Consulted | Product, Standards Team |
| Informed | All stakeholders |

## Context and Problem Statement

The European Digital Credential initiative requires the ec-issuer to issue credentials in **SD-JWT VC** format (European Learner Model / EDC), alongside the existing **Open Badges v3** (OBv3) format. Both formats share the same underlying `ssi-agent` issuance service but differ in their data structures, template IDs, and client API contracts.

The service must:

- Accept a `credential_type` field in API requests to let the caller choose between `ob3` and `edc`.
- Issue the correct format based on that choice.
- Default to `ob3` for backward compatibility with existing clients.
- Support both formats from a single `ssi-agent` instance without introducing a gateway or router.

## Decision Drivers

- Single shared `ssi-agent` instance (no gateway/router overhead).
- Backward compatibility — existing OBv3 clients must continue working unchanged.
- Clean separation between OBv3 and EDC data flows at the port/adaptor level.
- Simple configuration — EDC template discovery via sorted JSON files in a directory.
- Key management/KMS is out of scope for this iteration.

## Considered Options

- **Option A — Add `credential_type` to request body** (chosen): Extend the existing `/api/v1/offers` endpoint with an optional `credential_type` field defaulting to `"ob3"`. Split the offers port into `create_ob3()` and `create_edc()`. Dispatch in the service layer.
- **Option B — Separate endpoints**: Create `/api/v1/offers/ob3` and `/api/v1/offers/edc` as distinct routes. More explicit but more API surface and duplication.
- **Option C — Header-based selection**: Use a custom header (`X-Credential-Type`) instead of a request body field. Keeps the body clean but is less discoverable and harder to test with tools like `curl`.

## Decision Outcome

Chosen option: **"Option A — Add credential_type to request body"**, because:

- It extends the existing API without adding routes, keeping the surface minimal.
- The default `"ob3"` preserves backward compatibility — callers omitting the field get OBv3 as before.
- The service-layer dispatch (`_dispatch_create_offer`) cleanly routes to the correct port method.
- E2E tests can be parameterized over `credential_type` from a single test function.

### Consequences

- **Good**: Single endpoint, backward compatible, clean port split, easy to extend with future credential types.
- **Good**: Template discovery is order-independent (sorted JSON files in a directory guarantee index 0 = OB3, index 1 = EDC).
- **Bad**: The offers client port now has two methods instead of one — a small increase in interface complexity.
- **Bad**: The service-layer `_ob3_to_edc` mapping function adds a transient transformation layer that must stay in sync with both models.

## Validation

- All 110 unit tests pass (including tests for both `create_ob3` and `create_edc` flows).
- Integration tests parameterized to exercise both credential types.
- E2E tests use `credential_type` parameterization.
- `just lint` passes (ruff + basedpyright).

## Pros and Cons of the Options

### Option A — Add `credential_type` to request body (chosen)

- Good, because: backward compatible, minimal API surface, simple to test.
- Good, because: service-layer dispatch is straightforward and type-safe.
- Good, because: default value preserves existing client behavior.

### Option B — Separate endpoints

- Good, because: fully explicit — no defaults or optional fields.
- Bad, because: doubles API surface, duplicating auth/validation logic.
- Bad, because: existing clients must update to call the correct endpoint.

### Option C — Header-based selection

- Good, because: keeps request body clean for OBv3-only callers.
- Bad, because: less discoverable, harder to test with `curl`/Postman.
- Bad, because: headers are often invisible to API documentation tools.
