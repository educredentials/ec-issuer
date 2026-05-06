# Educredential Issuer

Credential service to issue **Open Badges 3.0** and **European Learner Model (ELM)** credentials.

## Development Environment
- Python, using uv, ruff and basedpyright
- Justfile and just for common tasks

### Just
run common commands with `just`. See `just --list` for a list of available commands. a few important ones:
 
- develop                    # Run the application in development mode. Command blocks, so use backgrounding `&` if needed.
- dependencies               # (re)start dependency services
- docs                       # Run mdbook to preview the docs
- lint                       # Run all quality checks
- test                       # Run all tests

## Project Structure

- src/ application code. The main entry point is `src/main.py`. See below _Running the app_ for details on how to run.
- tests/ test code. See below _Testing Instructions_ for details.
- docs/ documentation, glossary, overview and backgrounds, uses mdbook structure. Contains symlinks to files elswhere in this project.
- docs/src/adr Architecture Decision Records, ADRs.

### Running the app

podman compose runs the services that this application depends on, and can run
the service itself as well.

- `just dependencies` to (re)start all services except the ec-issuer.
- `just develop` to start the ec-issuer in development mode.
- `just develop-podman` to (re)start the services
- `just develop-real-agent` to (re)start the services with a real, instead of mocked agent.


## Important basic rules you may NEVER violate

- Use `just` to run tasks.
- Use `uv` only for dependency management. Never use pip or poetry.
- Never run `python` directly. When just or uv don't suffice, reconsider what you are solving. When stuck ask user for guidence.
- Use `podman compose` and `podman` for lower level container management and inspection.
- Never make bash scripts to run code.
- Only commit code that has no linting and typing errors. Never commit without checking `just lint` one last time.
- Only commit code that passes all tests. Never commit without running `just test` one last time and seeing all tests pass.
- If you get stuck, don't violate these rules, instead ask for guidance.

If you find yourself running python, custom bash scripts, python scripts, pip, pyenv or poetry you are vioalting the project rules and probably will severely break the project.

## Code Style Guidelines

- ruff defaults. Check with `just lint`. Format with `uv run ruff format`
- basedpyright defaults. Check with `just lint`. Some general guidelines to adhere to these basedpyright defaults:
  - never use Any
  - never use Unknown or partially Unknown
- Structured in modules, following the Screaming Architecture pattern.
- Follows Hexagonal Architecture with Ports and Adapters.
- Do not add comments to code that explain **what** the code does. Only add
  comments **why** we do it this way, if that is unclear, unexpected or uncommon.
- Make the code self-documenting by using good naming and structure.

## Lower level code guidelines

- response.json() from `request` lib is Any or Partially unknown. Avoid this. Use msgspec and Dataclasses instead
- use ABC for adapters. Python lacks interfaces, ABC is how we mimic interfaces.
- use `_UnderScore`, `_UNDERSCORE`, `_under_score()` etc to mark internals in
  modules as private. Python lacks visibility scoping, we mimic that with the
  underscore convention. Ruff and BasedPyright use that convention.

## Project Context

- Wrapper around third party issuance service that holds our
  business logic, hides third party details and provides a clean, pragmatic API.
- Integrates our services with this third party issuance service

## Testing Instructions

- Ensure the dependecies are running. See above, _Running the app_.
- Ensure the ec-issuer service is running. See above, _Running the app_.
- Run tests with `just test`.
- Do not run tests in isolation. Run them all.
- Do not run tests with `python` or `uv` commands. Only through just.
- Use the `/python-tdd` skill

## Linting and Typing Instructions

- Run linter with `just lint`.
- All errors and all warning must be fixed.
- Never add pyright ignore comments. When you cannot solve a typing error, ask the human for instructions instead of adding ignore comments.

## Ask for permission or guidance

- For any architectural change, stop and ask the human. Provide alternatives and describe their pros and cons.
- Exceptions to the guidelines and pitfalls are not allowed without explicit permission from the human. Stop and ask and give context on why we need an exception.

## Common Pitfalls to Avoid

- DON'T: Create new files unless necessary
- DON'T: Use print, logging to stdout for debugging. Prefer tests
- DON'T: Ignore linting and type checking errors or warnings
- DON'T: Revert or overwrite existing changes in files without explicit instructions. Other agents or a human, may be working on something as well.
- DO: Add type hints to all code
- DO: Add pydocstring to all functions and classes
- DO: Check existing components before creating new ones
- DO: Remove existing pyright-ignore comments and replace then with proper type hints, typing or other solutions
- DO: Follow established patterns in the codebase
- DO: Keep functions small and focused
