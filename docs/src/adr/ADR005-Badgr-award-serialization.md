# ADR005: Serialize Badgr API response as DTO before mapping to Award

| | |
|---|---|
| Status | accepted |
| Date | 2026-08-07 |
| Deciders | Daniel Ostkamp |
| Consulted | - |
| Informed | - |

## Context and Problem Statement

The Badgr awards API returns a JSON response with a schema significantly different from the OB3 `Award` domain model we expose. Key differences: integer `id` vs string entity_id, snake_case keys (`issued_on`, `badgeclass`), nested `badgeclass`/`issuer` objects with language-specific fields (`name_dutch`, `name_english`), and an `entity_id` that is our preferred ID over the integer `id`.

The previous mapping was a single function doing raw `dict[str, object]` indexing with manual `isinstance` guards. This made it hard to test because any schema change from the awards service silently produced incorrect mappings.

## Decision

Use msgspec `Struct` DTOs to strictly deserialize the Badgr JSON response before mapping to our OB3 `Award` domain model.

Three layers:
1. **DTO layer**: `_BadgrAwardResponse`, `_BadgrBadgeclass`, `_BadgrIssuer` as msgspec Structs — validated at HTTP boundary via `msgspec.json.decode(response.content, type=_BadgrAwardResponse)`
2. **Converter**: `_to_ob3_award(dto)` — pure function from DTO to OB3 domain model
3. **Public API**: `award_from_badgr_api_response(raw: dict)` — kept for backwards compatibility, delegates to DTO then converter

### Consequences

* Good, because msgspec raises `ValidationError` at the HTTP boundary if the Badgr response schema changes unexpectedly
* Good, because `_to_ob3_award()` is tested independently with plain DTO objects, no JSON parsing involved
* Good, because the DTO types express the Badgr API contract explicitly
* Good, because `msgspec.Struct` handles unknown fields by ignoring them, so new Badgr fields don't break us
* Bad, because adds a serialization step between HTTP response and domain model
* Neutral, because the DTO types are private (`_` prefix) and internal to `src.awards.models`

### Badgr DTO Schema

```
_BadgrAwardResponse (id: int, entity_id: str \| None, name: str \| None, issued_on: str \| None, badgeclass: _BadgrBadgeclass \| None)
  └── _BadgrBadgeclass (id: int, name: str, entity_id: str \| None, issuer: _BadgrIssuer \| None)
        └── _BadgrIssuer (name_dutch: str \| None, name_english: str \| None, faculty: str \| None)
```

### Badgr → OB3 Field Mapping

| Badgr field | OB3 Award field |
|---|---|
| `entity_id` → else `str(id)` | `id`, `credentialSubject.id`, `achievement.id` |
| `name` → else `badgeclass.name` → else `""` | `name`, `issuer.name`, `achievement.name` |
| `issued_on` | `validFrom` |
| `badgeclass.name` | `issuer.name`, `achievement.name` (fallback) |

## Implementation

The adapter decodes directly to `_BadgrAwardResponse` at the HTTP boundary:

```python
dto = msgspec.json.decode(response.content, type=_BadgrAwardResponse)
return _to_ob3_award(dto)
```

The public `award_from_badgr_api_response(raw: dict)` delegates for backwards compatibility:

```python
def award_from_badgr_api_response(raw: dict[str, object]) -> Award:
    dto = _BadgrAwardResponse.from_dict(raw)
    return _to_ob3_award(dto)
```
