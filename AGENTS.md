# Agent Instructions

Before making code, documentation, configuration, or test changes in this repository, read and follow the project standards.

## Always read (small, high-value core)

- `CODING_STANDARDS.md` — the source of truth for structure, conventions, verification commands, and Commits.
- `docs/glossary.md` — when naming anything domain-related: models, fields, functions, endpoints, endpoint paths.

## Read conditionally, by what you touch

- `BACKEND_STANDARDS.md` — before writing or editing any code in `backend/`.
- `docs/api-contracts.md` — before adding or modifying any endpoint.
- `docs/testing-standards.md` — before writing any test, in any stack.
- `docs/error-handling-and-logging.md` — before writing error handling or logging in any stack.
- `docs/git-workflow.md` — before branching, worktrees, commits, or opening a PR.
- `docs/superpowers/templates/spec-template.md` and `docs/superpowers/templates/plan-template.md` — before writing a new spec or implementation plan in `docs/superpowers/`.

## Key requirements

- Keep generated code consistent with the existing FastAPI, Python ML, React web, React Native mobile, Docker, and GitHub Actions structure.
- Use Conventional Commits for all commits.
- Run the package-specific verification commands listed in `CODING_STANDARDS.md` before claiming work is complete.
- Do not commit secrets, generated build artifacts, local caches, or large raw datasets.
- Update documentation when setup, commands, APIs, source-data assumptions, or workflows change.
- Keep new code conforming to the target contracts in the docs above; do not copy non-conforming patterns from existing code that has a documented "Known deviations" bullet.