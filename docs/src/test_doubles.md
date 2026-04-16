# Test Doubles

Test doubles are objects that stand in for real dependencies in unit tests.
All shared test doubles live in `tests/unit/test_doubles.py`.

## Naming Conventions

### Stub

Returns a hardcoded, preprogrammed response. Does **not** record how it was called.

Use when a dependency must satisfy a type contract but its exact behaviour is irrelevant to the test.

**Examples:** `AccessControlStub`, `ConfigRepoStub`, `MetadataServiceStub`

### Spy

Records how it was called **and** returns a preprogrammed response (or delegates to a real implementation). Lets the test assert on interactions.

Use when the test needs to verify that a collaborator was called with specific arguments.

**Examples:** `IssuerAgentSpy`, `OfferServiceSpy`

### Dummy

Satisfies a type constraint but is never actually invoked. Carries no behaviour.

Use when a dependency is required by a constructor but irrelevant to the behaviour under test.

### Mock

Returns a response based on logic — essentially a lightweight rule engine. Rarely needed; prefer a Spy or Stub instead.

## Rules

- Doubles live in `tests/unit/test_doubles.py`, not scattered across individual test files.
- Test-specific inline doubles (e.g. a `SpyAccessControl` inside a single test) are acceptable when they are too narrow to share.
- Do **not** use production hardcoded adapters (e.g. `HardcodedAccessControlAdapter`) as test doubles. They exist for development convenience, not for tests.
- If a double is getting complex, it is a sign the collaborator's API should be simplified instead.
