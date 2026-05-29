# Interface Design for Testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them**

   Depend on a Port (ABC), not a concrete adapter. Inject at construction time.

   ```python
   # Testable: dependency is injected, can be swapped in tests
   class OrderService:
       def __init__(self, payment_gateway: PaymentGatewayPort) -> None:
           self._payment_gateway = payment_gateway

   # Hard to test: creates its own dependency internally
   class OrderService:
       def __init__(self) -> None:
           self._payment_gateway = StripeGateway(settings.STRIPE_KEY)
   ```

2. **Return results, don't produce side effects**

   ```python
   # Testable: assert on the return value
   def calculate_discount(cart: Cart) -> Discount:
       ...

   # Hard to test: must inspect state after the call
   def apply_discount(cart: Cart) -> None:
       cart.total -= _compute_discount(cart)
   ```

3. **Small surface area**
   - Fewer methods = fewer tests needed
   - Fewer params = simpler test setup
   - Hide complexity behind `_` prefixed helpers (see [deep-modules.md](deep-modules.md))
