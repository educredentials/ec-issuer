# End-to-End Testing

End-to-end tests verify complete, user-visible journeys through the running system. They make real HTTP requests against all services and assert on observable outcomes — what a user or API consumer would see.

## When to write e2e tests

Write an e2e test for new features and for user-facing bugs that are common or visible enough to affect users in production. See the [TDD skill](../../.agent/skills/python-tdd/SKILL.md) for the full decision guide on when to use e2e vs integration vs unit tests.

## Running Tests

```bash
just test-e2e
```

This starts all required services via Podman Compose and waits for them to be healthy before running the test suite. Test fixtures never start or stop services themselves — if services are not running the tests fail with a clear connection error.

## Organisation

One test file per business feature in `tests/e2e/`, no subdirectories. Support files (JSON schemas, key material, shared fixtures) live alongside the test files in the same directory.
