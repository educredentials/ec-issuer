# Refactor Candidates

After TDD cycle, look for:

- **Duplication** → Extract function/class
- **Long methods** → Break into `_` prefixed private helpers (keep tests on the public interface)
- **Shallow modules** → Combine or deepen
- **Feature envy** → Move logic to where data lives
- **Primitive obsession** → Introduce value objects as `@dataclass(frozen=True)`
- **Existing code** the new code reveals as problematic

## Lint and Type Checks Are Non-Negotiable

All code must be warning- and error-free. Run `just lint` after every refactor step. This covers both ruff (style, imports, common errors) and basedpyright (type checking). Do not suppress warnings with ignore comments — fix the underlying issue. If you cannot resolve a type error, stop and ask.
