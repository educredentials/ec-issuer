# Educredential Issuer

Credential service to issue **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

## Development Environment
- Python, using uv, ruff and basedpyright
- Justfile and just for common tasks

## Project Structure
- src/ application code. The main entry point is `src/main.py`. Run with `just develop`
- tests/ test code. Run with `just test`
- docs/ documentation, guidelines and ADRs

## Code Style Guidelines
- ruff defaults. Check with `uv run ruff check`. Format with `uv run ruff format`
- basedpyright defaults. Check with `uv run basedpyright`.
- Structured in modules, following the Screaming Architecture pattern.
- Follows Hexagonal Architecture with Ports and Adapters.
- Do not add comments to code that explain **what** the code does.
- Make the code self-documenting by using good naming and structure.

## Project Context
- Wrapper around third party issuance service that holds our
  business logic, hides third party details and provides a clean, pragmatic API.
- Integrates our services with this third party issuance service

## Testing Instructions
- Use the test-driven-development skill. Stop and report if you cannot find this skill.
- End to end tests each get a file/module per business feature in `tests/e2e` no subdirectories
- Integration and unit tests under test/unit/<module_name>. The files follow the structure of the src/ directory
- Run tests with `just test`

## Ask for permission or guidance
- For any architectural change, stop and ask the human. Provide alternatives and describe their pros and cons.
- Exceptions to the guidelines and pitfalls are not allowed without explicit permission from the human. Stop and ask and give context on why we need an exception.

## Common Pitfalls to Avoid

- DON'T: Create new files unless necessary
- DON'T: Use print, logging to stdout for debugging. Prefer tests
- DON'T: Ignore linting and type checking errors or warnings
- DON'T: add pyright ignore comments
- DON'T: Skip tests for "simple" features
- DO: Add type hints to all code
- DO: Add pydocstring to all functions and classes
- DO: Check existing components before creating new ones
- DO: Follow established patterns in the codebase
- DO: Keep functions small and focused
