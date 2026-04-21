# Educredential Issuer

Credential service to issue **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

## Development Environment
- Python, using uv, ruff and basedpyright
- Justfile and just for common tasks

## Project Structure
- run common commands with `just`. `just --list` returns:
  all                        # Run everything (lint + test)
  default                    # Default target
  docs                       # Run mdbook to preview the docs.
  lint                       # Run all quality checks (linting + type checking)
  test                       # Run all tests
  test-e2e                   # Run only e2e tests, Note: starts a test server
  test-unit                  # Run only unit tests
- src/ application code. The main entry point is `src/main.py`. Run with `just develop`
- tests/ test code.
- docs/ documentation, guidelines and ADRs

## Code Style Guidelines
- ruff defaults. Check with `just lint`. Format with `uv run ruff format`
- basedpyright defaults. Check with `just lint`.
- Structured in modules, following the Screaming Architecture pattern.
- Follows Hexagonal Architecture with Ports and Adapters.
- Do not add comments to code that explain **what** the code does.
- Make the code self-documenting by using good naming and structure.

## Project Context
- Wrapper around third party issuance service that holds our
  business logic, hides third party details and provides a clean, pragmatic API.
- Integrates our services with this third party issuance service

## Testing Instructions
- Run tests with `just test`
- Use the test-driven-development skill. Stop and report if you cannot find this skill.
- End to end tests each get a file/module per business feature in `tests/e2e` no subdirectories
- Integration and unit tests under test/unit/<module_name>. The files follow the structure of the src/ directory

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
