# When to Mock

Mock at **system boundaries** only:

- External APIs (payment, email, third-party services)
- Databases (prefer a real test DB; use an in-memory adapter when that's impractical)
- Time / randomness
- File system (sometimes)

Don't mock:

- Your own modules or classes
- Internal collaborators
- Anything you control

## Test Double Types

Use the naming conventions from `tests/unit/test_doubles.py`:

- **Stub** — returns a hardcoded response, does not record calls. Use when a collaborator must satisfy a type contract but its behaviour is irrelevant to the test.
- **Spy** — records how it was called and returns a preprogrammed response. Use when the test needs to assert that a collaborator was called with specific arguments.
- **Mock** — returns a response based on conditional logic (a lightweight rule engine). Use sparingly; prefer Stub or Spy.
- **Dummy** — satisfies a type constraint but is never invoked. Use when a dependency is required by a constructor but irrelevant to the test.

Shared doubles live in `tests/unit/test_doubles.py`. Test-specific inline doubles are acceptable when they are too narrow to share.

## Designing for Testability with Ports and Adapters

The cleanest way to make code testable at system boundaries is to define a **Port** (an `ABC`) and inject it. Tests pass a double that implements the same port; production code passes the real adapter.

```python
from abc import ABC, abstractmethod

# The port — defines what the module needs
class PaymentGatewayPort(ABC):
    @abstractmethod
    def charge(self, amount: int) -> Receipt: ...

# Production adapter — talks to the real payment provider
class StripeAdapter(PaymentGatewayPort):
    def charge(self, amount: int) -> Receipt:
        # real Stripe API call
        ...

# Test stub — satisfies the port, returns hardcoded data
class PaymentGatewayStub(PaymentGatewayPort):
    def charge(self, amount: int) -> Receipt:
        return Receipt(status="confirmed", amount=amount)

# Test spy — records the call so we can assert on it
class PaymentGatewaySpy(PaymentGatewayPort):
    last_charge: int | None = None

    def charge(self, amount: int) -> Receipt:
        self.last_charge = amount
        return Receipt(status="confirmed", amount=amount)
```

The service under test accepts the port, not the concrete adapter:

```python
class OrderService:
    def __init__(self, payment_gateway: PaymentGatewayPort) -> None:
        self._payment_gateway = payment_gateway

    def checkout(self, cart: Cart) -> Receipt:
        return self._payment_gateway.charge(cart.total)
```

In tests:

```python
# Unit test: verify behavior, use a stub
def test_checkout_returns_confirmed_receipt():
    service = OrderService(payment_gateway=PaymentGatewayStub())
    result = service.checkout(cart_with_total(100))
    assert result.status == "confirmed"

# Unit test: verify interaction, use a spy
def test_checkout_charges_correct_amount():
    spy = PaymentGatewaySpy()
    service = OrderService(payment_gateway=spy)
    service.checkout(cart_with_total(250))
    assert spy.last_charge == 250
```

## In-Memory Adapters for Integration Tests

For integration tests, prefer a real in-memory adapter over a stub. It exercises real logic (creating, storing, retrieving) without infrastructure:

```python
class InMemoryJokesRepository(JokesRepositoryPort):
    def __init__(self) -> None:
        self._jokes: list[Joke] = []

    def get_jokes(self) -> list[Joke]:
        return self._jokes

    def create_joke(self, joke: Joke) -> Joke:
        self._jokes.append(joke)
        return joke
```

This is not a mock — it has real behaviour. Use it in integration tests to wire modules together without touching a real database.

## SDK-Style Interfaces Over Generic Fetchers

Create specific methods for each external operation instead of one generic method:

```python
# GOOD: each method is independently testable and stubbable
class CredentialAgentPort(ABC):
    @abstractmethod
    def create_offer(self, credential: Credential) -> Offer: ...

    @abstractmethod
    def get_offer_status(self, offer_id: str) -> OfferStatus: ...

# BAD: mocking requires conditional logic inside the double
class CredentialAgentPort(ABC):
    @abstractmethod
    def call(self, endpoint: str, payload: dict[str, object]) -> dict[str, object]: ...
```

Specific methods mean each stub or spy returns one well-typed shape, with no conditional logic in test setup.
