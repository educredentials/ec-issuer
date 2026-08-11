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

### Call Chain

```
HTTP Handler (extract bearer from Authorization header)
  → OfferService.get_offer(award_id, bearer_token)
    → AwardService.get(award_id, bearer_token)
      → AwardsClientPort.get(award_id, bearer_token)
        → HttpAwardsClientAdapter.get(award_id, bearer_token)
          → http_client.get(url, headers={"Authorization": f"Bearer {bearer_token}"})
```

### HTTP Client Protocol Extension

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

### Consequences

* Good, because the token flows naturally through existing services without new configuration
* Good, because the token is not stored or logged — it is forwarded request-to-request
* Good, because the HTTP client protocol supports headers on all methods (`get`, `post`, `delete`) via the existing `**kwargs` pattern
* Bad, because every caller in the chain must carry and propagate the token parameter
* Bad, because the public `HttpClient.get()` signature changed from one to two positional parameters (the second is keyword-only-ish, but still a signature change)
