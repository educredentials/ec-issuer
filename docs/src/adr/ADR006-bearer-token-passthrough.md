# ADR006: Pass bearer token through awards client chain

| | |
|---|---|
| Status | accepted |
| Date | 2026-08-07 |
| Deciders | Daniel Ostkamp |
| Consulted | - |
| Informed | - |

## Context and Problem Statement

The awards service (Badgr) requires per-request authentication. The ec-issuer receives a bearer token from the end user via the offers endpoint. This token must be forwarded to the awards service so it can verify the caller has access to the requested award.

Previously the awards client had no authentication at all — `get(award_id)` made unauthenticated requests.

## Decision

Pass the bearer token through the entire awards client chain using an optional `headers` parameter on the HTTP client protocol, forwarded as `Authorization: Bearer <token>`.

## Considered Options

* **Pass token as explicit parameter** — add `bearer_token` parameter to each interface method in the chain (`AwardService`, `AwardsClientPort`, `HttpAwardsClientAdapter`)
* **Thread-local storage** — store the token in a thread-local context at the HTTP handler and retrieve it deep in the call chain
* **Pass token as `headers` dict** — extend the `HttpClient` protocol with an optional `headers` parameter

## Decision Outcome

Chosen option: "Pass token as `headers` dict", because it routes the token through the HTTP client layer (its only usage boundary) and avoids polluting domain interfaces with auth concerns.

## Pros and Cons of the Options

### Pass token as explicit parameter

* Good, because no changes to the HTTP client protocol
* Bad, because `bearer_token` must be threaded through every layer of the awards client chain
* Bad, because domain interfaces (`OfferService`, `AwardService`) leak auth concerns
* Bad, because every caller must remember to pass the token or risk unauthenticated requests

### Thread-local storage

* Neutral, because it avoids passing the token through the call chain
* Bad, because thread-local state is harder to reason about and test
* Bad, because the token could accidentally leak into unrelated requests
* Bad, because it hides the data flow from the type system

### Pass token as `headers` dict

* Good, because the token is handled at the HTTP layer where it belongs
* Good, because domain logic remains unaware of authentication concerns
* Good, because the existing `**kwargs` pattern on the client protocol keeps the change minimal
* Bad, because every caller must still carry and propagate the token argument down to the adapter

## Call Chain

```
HTTP Handler (extract bearer from Authorization header)
  → OfferService.get_offer(award_id, bearer_token)
    → AwardService.get(award_id, bearer_token)
      → AwardsClientPort.get(award_id, bearer_token)
        → HttpAwardsClientAdapter.get(award_id, bearer_token)
          → http_client.get(url, headers={"Authorization": f"Bearer {bearer_token}"})
```

## HTTP Client Protocol Extension

The `HttpClient` protocol was extended with an optional `headers` parameter:

```python
class HttpClient(Protocol):
    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse: ...
```

`RequestsHttpClient` forwards `headers` to `requests.request()` via `**kwargs`. Test doubles (`RequestsSpy`) record headers in their `calls` list.

## Consequences

* Good, because the token flows naturally through existing services without new configuration
* Good, because the token is not stored or logged — it is forwarded request-to-request
* Good, because the HTTP client protocol supports headers on all methods (`get`, `post`, `delete`) via the existing `**kwargs` pattern
* Bad, because every caller in the chain must carry and propagate the token parameter
* Bad, because the public `HttpClient.get()` signature changed from one to two positional parameters (the second is keyword-only-ish, but still a signature change)
