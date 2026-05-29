# Good and Bad Tests

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```python
# GOOD: Tests observable behavior
class TestCheckout:
    def test_user_can_checkout_with_valid_cart(self):
        cart = Cart()
        cart.add(product)
        result = checkout(cart, payment_method)
        assert result.status == "confirmed"
```

Characteristics:

- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```python
# BAD: Tests implementation details
class TestCheckout:
    def test_checkout_calls_payment_service(self):
        payment_spy = PaymentServiceSpy()
        checkout(cart, payment_spy)
        assert payment_spy.process_called_with == cart.total
```

Red flags:

- Mocking internal collaborators
- Testing private methods (anything prefixed `_`)
- Asserting on call counts/order when behavior is what matters
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface

```python
# BAD: Bypasses interface to verify
def test_create_user_saves_to_database():
    create_user(name="Alice")
    row = db.execute("SELECT * FROM users WHERE name = ?", ["Alice"])
    assert row is not None

# GOOD: Verifies through interface
def test_create_user_makes_user_retrievable():
    user = create_user(name="Alice")
    retrieved = get_user(user.id)
    assert retrieved.name == "Alice"
```

## Testing Pyramid

Keep the pyramid in mind: **few e2e tests, more integration tests, many unit tests.**

```
        /\
       /e2e\        ← few, slow, broad
      /------\
     / integr \     ← moderate, test module interactions
    /----------\
   /    unit    \   ← many, fast, specific
  /--------------\
```

Ports and Adapters make this work. Business logic modules have no infrastructure dependencies, so they can be unit-tested by passing in-memory adapters — no network, no database, no mocks needed. See [SKILL.md](SKILL.md) for when to use each level.

## Folder Structure

Unit and integration tests mirror the `src/` structure:

```
src/
  issuer_agent/
    ssi_agent_adapter.py
  metadata/
    metadata_repository.py

tests/
  unit/
    issuer_agent/
      test_ssi_agent_adapter.py
    metadata/
      test_metadata_repository.py
  integration/
    test_metadata_repository.py   # tests module interactions
  e2e/
    test_credential_issuance.py   # one file per business feature
```

- `tests/unit/` must mirror `src/` exactly — one test file per source file, same directory depth.
- `tests/e2e/` has one file per business feature, no subdirectories.

## Support Infrastructure

### E2e tests (`tests/e2e/`)

The e2e directory contains support utilities alongside test files: JSON schemas for validating responses, key material for authentication flows, and shared fixtures in `conftest.py`. Before adding new support files, check what already exists there — reuse schemas, helpers, and fixtures rather than duplicating them.

### Unit tests (`tests/unit/`)

Shared test doubles (Stub, Spy, Mock, Dummy) live in `tests/unit/test_doubles.py`. Shared fixtures live in `tests/unit/conftest.py`. Check both before writing new doubles or fixtures. See [mocking.md](mocking.md) for test double conventions.
